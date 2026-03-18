"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";

export async function pauseOutreachMessage(id: number) {
  const msg = await prisma.outreach_messages.findUnique({ where: { id } });
  if (!msg) return { error: "Message not found." };
  if (msg.status === "completed") return { error: "Cannot pause a completed message." };

  await prisma.outreach_messages.update({
    where: { id },
    data: { status: "paused", paused_at: new Date(), updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true };
}

export async function resumeOutreachMessage(id: number) {
  const msg = await prisma.outreach_messages.findUnique({ where: { id } });
  if (!msg) return { error: "Message not found." };
  if (msg.status === "completed") return { error: "Cannot resume a completed message." };

  await prisma.outreach_messages.update({
    where: { id },
    data: { status: "launched", paused_at: null, launched_at: msg.launched_at ?? new Date(), updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true };
}

export async function launchOutreachMessage(id: number) {
  const msg = await prisma.outreach_messages.findUnique({ where: { id } });
  if (!msg) return { error: "Message not found." };
  if (msg.status !== "pending") return { error: "Only pending messages can be launched." };

  await prisma.outreach_messages.update({
    where: { id },
    data: { status: "launched", launched_at: new Date(), updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true };
}

export async function stopOutreachMessage(id: number) {
  const msg = await prisma.outreach_messages.findUnique({ where: { id } });
  if (!msg) return { error: "Message not found." };
  if (msg.status === "completed") return { error: "Message is already stopped." };

  await prisma.outreach_messages.update({
    where: { id },
    data: { status: "completed", updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true };
}

export async function bulkPauseOutreach(filters: { status?: string; platform?: string }) {
  const where: any = { status: "launched" };
  if (filters.platform) where.platform = filters.platform;

  const result = await prisma.outreach_messages.updateMany({
    where,
    data: { status: "paused", paused_at: new Date(), updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true, count: result.count };
}

export async function bulkResumeOutreach(filters: { status?: string; platform?: string }) {
  const where: any = { status: "paused" };
  if (filters.platform) where.platform = filters.platform;

  const result = await prisma.outreach_messages.updateMany({
    where,
    data: { status: "launched", paused_at: null, updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true, count: result.count };
}

export async function bulkStopOutreach(filters: { status?: string; platform?: string }) {
  const where: any = { status: { not: "completed" } };
  if (filters.platform) where.platform = filters.platform;
  if (filters.status && filters.status !== "completed") where.status = filters.status;

  const result = await prisma.outreach_messages.updateMany({
    where,
    data: { status: "completed", updated_at: new Date() },
  });

  revalidatePath("/outreach");
  return { success: true, count: result.count };
}
