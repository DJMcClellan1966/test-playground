// Auto-generated from Task contract
// Hash: c1bf2387

export interface Task {
  title: string;
  done: boolean;
}

export const TaskSchema = {
  title: { type: 'string', required: true },
  done: { type: 'boolean', required: true },
};