"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";

export async function createEmailAccount(formData: FormData) {
  const email_address = formData.get("email_address") as string;
  const display_name = formData.get("display_name") as string;
  const platform = formData.get("platform") as string;
  const warmup_status = (formData.get("warmup_status") as string) || "pending";
  const daily_send_limit = parseInt(formData.get("daily_send_limit") as string) || 30;

  if (!email_address || !display_name || !platform) {
    return { error: "Email, display name, and platform are required." };
  }

  try {
    await prisma.email_accounts.create({
      data: { email_address, display_name, platform, warmup_status, daily_send_limit },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "This email address already exists." };
    return { error: "Failed to create email account." };
  }

  revalidatePath("/settings/email-accounts");
  return { success: true };
}

export async function updateEmailAccount(id: number, formData: FormData) {
  const email_address = formData.get("email_address") as string;
  const display_name = formData.get("display_name") as string;
  const platform = formData.get("platform") as string;
  const warmup_status = formData.get("warmup_status") as string;
  const daily_send_limit = parseInt(formData.get("daily_send_limit") as string) || 30;

  try {
    await prisma.email_accounts.update({
      where: { id },
      data: { email_address, display_name, platform, warmup_status, daily_send_limit, updated_at: new Date() },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "This email address already exists." };
    return { error: "Failed to update email account." };
  }

  revalidatePath("/settings/email-accounts");
  return { success: true };
}

export async function toggleEmailAccount(id: number) {
  const account = await prisma.email_accounts.findUnique({ where: { id } });
  if (!account) return { error: "Account not found." };

  await prisma.email_accounts.update({
    where: { id },
    data: { is_active: !account.is_active, updated_at: new Date() },
  });

  revalidatePath("/settings/email-accounts");
  return { success: true };
}

export async function deleteEmailAccount(id: number) {
  await prisma.email_accounts.delete({ where: { id } });
  revalidatePath("/settings/email-accounts");
  return { success: true };
}
