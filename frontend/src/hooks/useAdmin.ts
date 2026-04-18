import { useState, useCallback } from "react";
import { verifyAdmin } from "../api/masters";

const SESSION_KEY = "admin_mode";

export function useAdmin() {
  const [isAdmin, setIsAdmin] = useState<boolean>(sessionStorage.getItem(SESSION_KEY) === "1");

  const login = useCallback(async (password: string): Promise<boolean> => {
    const ok = await verifyAdmin(password);
    if (ok) {
      sessionStorage.setItem(SESSION_KEY, "1");
      setIsAdmin(true);
    }
    return ok;
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    setIsAdmin(false);
  }, []);

  return { isAdmin, login, logout };
}
