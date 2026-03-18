"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";

export async function createUser(formData: FormData) {
  const name = formData.get("name") as string;
  const email = formData.get("email") as string;
  const role = (formData.get("role") as string) || "recruiter";
  const slack_id = (formData.get("slack_id") as string) || null;

  if (!name || !email) {
    return { error: "Name and email are required." };
  }

  try {
    await prisma.users.create({
      data: { name, email, role, slack_id },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "A user with this email already exists." };
    return { error: "Failed to create user." };
  }

  revalidatePath("/settings/users");
  return { success: true };
}

export async function updateUser(id: number, formData: FormData) {
  const name = formData.get("name") as string;
  const email = formData.get("email") as string;
  const role = formData.get("role") as string;
  const slack_id = (formData.get("slack_id") as string) || null;

  try {
    await prisma.users.update({
      where: { id },
      data: { name, email, role, slack_id, updated_at: new Date() },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "A user with this email already exists." };
    return { error: "Failed to update user." };
  }

  revalidatePath("/settings/users");
  return { success: true };
}

export async function toggleUser(id: number) {
  const user = await prisma.users.findUnique({ where: { id } });
  if (!user) return { error: "User not found." };

  await prisma.users.update({
    where: { id },
    data: { is_active: !user.is_active, updated_at: new Date() },
  });

  revalidatePath("/settings/users");
  return { success: true };
}

export async function deleteUser(id: number) {
  await prisma.users.delete({ where: { id } });
  revalidatePath("/settings/users");
  return { success: true };
}
