"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";

const AUTOMATION_KEY = "scraping_automation_enabled";

export async function getAutomationStatus(): Promise<boolean> {
  const setting = await prisma.system_settings.findUnique({
    where: { key: AUTOMATION_KEY },
  });
  return setting?.value === "true";
}

export async function toggleAutomation() {
  const current = await getAutomationStatus();
  const newValue = !current;

  await prisma.system_settings.upsert({
    where: { key: AUTOMATION_KEY },
    update: { value: String(newValue), updated_at: new Date() },
    create: { key: AUTOMATION_KEY, value: String(newValue) },
  });

  revalidatePath("/scrape-runs");
  return { success: true, enabled: newValue };
}

export async function triggerScrapeRun(boardName?: string) {
  // Create a queued scrape run record. The backend worker picks these up.
  // If no board specified, create one for each enabled board.
  const boards = boardName ? [boardName] : await getEnabledBoards();

  const runs = [];
  for (const board of boards) {
    const run = await prisma.scrape_runs.create({
      data: {
        board_name: board,
        status: "queued",
        jobs_found: 0,
        jobs_new: 0,
        jobs_duplicate: 0,
        started_at: new Date(),
      },
    });
    runs.push(run);
  }

  revalidatePath("/scrape-runs");
  return { success: true, count: runs.length, boards };
}

async function getEnabledBoards(): Promise<string[]> {
  // Return the list of boards that have had successful scrape runs
  // This is a proxy for "enabled boards" without needing to read config.yaml
  const recentRuns = await prisma.scrape_runs.findMany({
    distinct: ["board_name"],
    orderBy: { started_at: "desc" },
    take: 20,
    select: { board_name: true },
  });

  if (recentRuns.length > 0) {
    return recentRuns.map((r) => r.board_name);
  }

  // Default boards if no history exists
  return [
    "greenhouse", "lever", "ashby", "workable", "smartrecruiters",
    "jazzhr", "jobvite", "wellfound", "bamboohr", "rippling",
    "icims", "recruiterbox", "workday", "linkedin", "indeed",
  ];
}
