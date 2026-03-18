"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";

export async function createTemplate(formData: FormData) {
  const name = formData.get("name") as string;
  const subject = (formData.get("subject") as string) || null;
  const body = formData.get("body") as string;
  const stage_number = parseInt(formData.get("stage_number") as string);
  const stage_label = (formData.get("stage_label") as string) || null;
  const platform = formData.get("platform") as string;
  const sequence_group = (formData.get("sequence_group") as string) || null;

  if (!name || !body || !stage_number || !platform) {
    return { error: "Name, body, stage, and platform are required." };
  }

  try {
    await prisma.outreach_templates.create({
      data: { name, subject, body, stage_number, stage_label, platform, sequence_group },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "A template with this sequence/stage/platform already exists." };
    return { error: "Failed to create template." };
  }

  revalidatePath("/settings/templates");
  return { success: true };
}

export async function updateTemplate(id: number, formData: FormData) {
  const name = formData.get("name") as string;
  const subject = (formData.get("subject") as string) || null;
  const body = formData.get("body") as string;
  const stage_number = parseInt(formData.get("stage_number") as string);
  const stage_label = (formData.get("stage_label") as string) || null;
  const platform = formData.get("platform") as string;
  const sequence_group = (formData.get("sequence_group") as string) || null;

  try {
    await prisma.outreach_templates.update({
      where: { id },
      data: { name, subject, body, stage_number, stage_label, platform, sequence_group, updated_at: new Date() },
    });
  } catch (e: any) {
    if (e.code === "P2002") return { error: "A template with this sequence/stage/platform already exists." };
    return { error: "Failed to update template." };
  }

  revalidatePath("/settings/templates");
  return { success: true };
}

export async function toggleTemplate(id: number) {
  const template = await prisma.outreach_templates.findUnique({ where: { id } });
  if (!template) return { error: "Template not found." };

  await prisma.outreach_templates.update({
    where: { id },
    data: { is_active: !template.is_active, updated_at: new Date() },
  });

  revalidatePath("/settings/templates");
  return { success: true };
}

export async function deleteTemplate(id: number) {
  await prisma.outreach_templates.delete({ where: { id } });
  revalidatePath("/settings/templates");
  return { success: true };
}
