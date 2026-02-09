// Auto-generated from User contract
// Hash: 28391d59

export interface User {
  id: string;
  email: string;
  username: string;
  password_hash: string;
}

export const UserSchema = {
  id: { type: 'string', required: true },
  email: { type: 'string', required: true, constraint: 'email' },
  username: { type: 'string', required: true, constraint: 'min:3' },
  password_hash: { type: 'string', required: true },
};