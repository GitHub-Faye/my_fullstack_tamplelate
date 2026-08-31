import { UserTable } from "../client/UserTable";

/**
 * UserList Server Component
 * Renders the client UserTable
 * Note: UserTable 内部通过 auth store 获取当前用户 id 以禁用"删除自己"，
 * 无需再从服务端透传 currentUserId。
 */
export async function UserList() {
  return <UserTable />;
}
