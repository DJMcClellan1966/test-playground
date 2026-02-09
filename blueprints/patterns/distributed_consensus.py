"""
Raft Consensus Algorithm (Simplified)
Expert-level project for distributed systems.

Raft ensures all nodes in a cluster agree on the same state,
even when some nodes fail. Used by: etcd, Consul, CockroachDB.

Key concepts:
1. Leader Election - one leader coordinates writes
2. Log Replication - leader sends entries to followers  
3. Safety - committed entries are durable
"""
import random
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable


class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    term: int
    command: str
    index: int


@dataclass
class RaftNode:
    """
    A single node in a Raft cluster.
    
    In production: nodes communicate over network.
    Here: we simulate with method calls.
    """
    node_id: str
    state: NodeState = NodeState.FOLLOWER
    current_term: int = 0
    voted_for: Optional[str] = None
    log: List[LogEntry] = field(default_factory=list)
    commit_index: int = 0
    
    # Leader state
    next_index: Dict[str, int] = field(default_factory=dict)
    match_index: Dict[str, int] = field(default_factory=dict)
    
    # Timing (simulated)
    election_timeout: float = 0
    last_heartbeat: float = 0
    
    def reset_election_timeout(self):
        """Random timeout between 150-300ms to prevent split votes"""
        self.election_timeout = random.uniform(0.15, 0.30)
        self.last_heartbeat = time.time()
    
    def start_election(self, cluster: 'RaftCluster'):
        """Become candidate, request votes from all nodes"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        votes = 1  # Vote for self
        
        print(f"[{self.node_id}] Starting election for term {self.current_term}")
        
        last_log_index = len(self.log) - 1 if self.log else -1
        last_log_term = self.log[-1].term if self.log else 0
        
        for node in cluster.nodes.values():
            if node.node_id != self.node_id:
                vote_granted = node.handle_request_vote(
                    self.current_term, 
                    self.node_id,
                    last_log_index,
                    last_log_term
                )
                if vote_granted:
                    votes += 1
        
        # Majority required
        if votes > len(cluster.nodes) // 2:
            self.become_leader(cluster)
        else:
            self.state = NodeState.FOLLOWER
    
    def handle_request_vote(self, term: int, candidate_id: str,
                           last_log_index: int, last_log_term: int) -> bool:
        """Handle vote request from candidate"""
        if term < self.current_term:
            return False
        
        if term > self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
        
        # Only vote if haven't voted yet and candidate's log is up-to-date
        if self.voted_for is None or self.voted_for == candidate_id:
            my_last_index = len(self.log) - 1 if self.log else -1
            my_last_term = self.log[-1].term if self.log else 0
            
            log_ok = (last_log_term > my_last_term or 
                     (last_log_term == my_last_term and last_log_index >= my_last_index))
            
            if log_ok:
                self.voted_for = candidate_id
                self.reset_election_timeout()
                print(f"[{self.node_id}] Voted for {candidate_id} in term {term}")
                return True
        
        return False
    
    def become_leader(self, cluster: 'RaftCluster'):
        """Transition to leader state"""
        self.state = NodeState.LEADER
        print(f"[{self.node_id}] Became LEADER for term {self.current_term}")
        
        # Initialize leader state
        for node_id in cluster.nodes:
            if node_id != self.node_id:
                self.next_index[node_id] = len(self.log)
                self.match_index[node_id] = 0
        
        # Send initial heartbeat
        self.send_heartbeats(cluster)
    
    def send_heartbeats(self, cluster: 'RaftCluster'):
        """Leader sends AppendEntries to all followers"""
        for node in cluster.nodes.values():
            if node.node_id != self.node_id:
                # AppendEntries with no new entries = heartbeat
                node.handle_append_entries(
                    self.current_term,
                    self.node_id,
                    len(self.log) - 1,
                    self.log[-1].term if self.log else 0,
                    [],  # No new entries for heartbeat
                    self.commit_index
                )
    
    def handle_append_entries(self, term: int, leader_id: str,
                             prev_log_index: int, prev_log_term: int,
                             entries: List[LogEntry], leader_commit: int) -> bool:
        """Handle AppendEntries from leader"""
        if term < self.current_term:
            return False
        
        self.reset_election_timeout()
        
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
        
        self.state = NodeState.FOLLOWER
        
        # Check log consistency
        if prev_log_index >= 0:
            if len(self.log) <= prev_log_index:
                return False
            if self.log[prev_log_index].term != prev_log_term:
                return False
        
        # Append new entries
        for entry in entries:
            if entry.index < len(self.log):
                # Overwrite conflicting entry
                self.log[entry.index] = entry
            else:
                self.log.append(entry)
        
        # Update commit index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)
        
        return True
    
    def client_request(self, command: str, cluster: 'RaftCluster') -> bool:
        """Handle client write request (leader only)"""
        if self.state != NodeState.LEADER:
            print(f"[{self.node_id}] Not leader, redirecting...")
            return False
        
        # Append to own log
        entry = LogEntry(
            term=self.current_term,
            command=command,
            index=len(self.log)
        )
        self.log.append(entry)
        
        print(f"[{self.node_id}] Appending: {command}")
        
        # Replicate to followers
        success_count = 1
        for node in cluster.nodes.values():
            if node.node_id != self.node_id:
                success = node.handle_append_entries(
                    self.current_term,
                    self.node_id,
                    len(self.log) - 2,
                    self.log[-2].term if len(self.log) > 1 else 0,
                    [entry],
                    self.commit_index
                )
                if success:
                    success_count += 1
        
        # Commit if majority replicated
        if success_count > len(cluster.nodes) // 2:
            self.commit_index = entry.index
            print(f"[{self.node_id}] Committed: {command}")
            return True
        
        return False


@dataclass
class RaftCluster:
    """Manages a cluster of Raft nodes"""
    nodes: Dict[str, RaftNode] = field(default_factory=dict)
    
    def add_node(self, node_id: str):
        node = RaftNode(node_id)
        node.reset_election_timeout()
        self.nodes[node_id] = node
    
    def get_leader(self) -> Optional[RaftNode]:
        for node in self.nodes.values():
            if node.state == NodeState.LEADER:
                return node
        return None


def demo():
    print("=== Raft Consensus Demo ===\n")
    
    # Create a 3-node cluster
    cluster = RaftCluster()
    for i in range(1, 4):
        cluster.add_node(f"node{i}")
    
    print("Created 3-node cluster\n")
    
    # Simulate node1 timing out and starting election
    node1 = cluster.nodes["node1"]
    node1.start_election(cluster)
    
    print()
    
    # Client writes to leader
    leader = cluster.get_leader()
    if leader:
        leader.client_request("SET x = 1", cluster)
        leader.client_request("SET y = 2", cluster)
    
    print("\n=== Final Log State ===")
    for node_id, node in cluster.nodes.items():
        entries = [f"({e.term}:{e.command})" for e in node.log]
        print(f"{node_id} [{node.state.value}]: {entries}")
    
    print("\n=== Key Concepts ===")
    print("1. Leader Election: Random timeouts, majority vote")
    print("2. Log Replication: Leader sends entries to followers")
    print("3. Commit: Entry committed when replicated to majority")
    print("4. Safety: Committed entries are never lost")


if __name__ == "__main__":
    demo()
