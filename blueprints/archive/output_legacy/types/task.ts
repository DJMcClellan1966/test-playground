// Auto-generated from Task contract
// Hash: 37615aaa

export interface Task {
  id: string;
  title: string;
  description?: string;
  priority: number;
  completed: boolean;
  user_id: string;
}

export const TaskSchema = {
  id: { type: 'string', required: true },
  title: { type: 'string', required: true, constraint: 'min:1' },
  description: { type: 'text' },
  priority: { type: 'integer', required: true, constraint: 'min:1', constraint: 'max:5' },
  completed: { type: 'boolean', required: true },
  user_id: { type: 'string', required: true },
};