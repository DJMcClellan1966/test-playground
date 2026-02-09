// Auto-generated from Team contract
// Hash: 9cde843f

export interface Team {
  id: string;
  name: string;
  member_ids: any[];
}

export const TeamSchema = {
  id: { type: 'string', required: true },
  name: { type: 'string', required: true },
  member_ids: { type: 'list', required: true },
};