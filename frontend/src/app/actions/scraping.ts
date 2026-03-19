"use server";

import { prisma } from "@/lib/prisma";
import { revalidatePath } from "next/cache";
import { exec } from "child_process";
import path from "path";

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
  // Spawn the Python scraper as a background process.
  // The script writes results directly to the shared Railway database.
  const projectRoot = path.resolve(process.cwd(), "..");
  const scriptPath = path.join(projectRoot, "scripts", "run_once.py");

  try {
    const command = `cd "${projectRoot}" && python3 "${scriptPath}" scrape`;

    // Fire-and-forget: spawn the process in the background
    exec(command, { timeout: 600_000 }, (error, stdout, stderr) => {
      if (error) {
        console.error("[scrape] Process error:", error.message);
      }
      if (stdout) {
        console.log("[scrape] Output:", stdout);
      }
      if (stderr) {
        console.error("[scrape] Stderr:", stderr);
      }
    });

    revalidatePath("/scrape-runs");
    return {
      success: true,
      message: "Scraping all boards in background — refresh in a few minutes to see results.",
    };
  } catch {
    // Fallback: on Vercel or if python is unavailable, just create queued records
    const boards = boardName ? [boardName] : await getEnabledBoards();
    for (const board of boards) {
      await prisma.scrape_runs.create({
        data: {
          board_name: board,
          status: "queued",
          jobs_found: 0,
          jobs_new: 0,
          jobs_duplicate: 0,
          started_at: new Date(),
        },
      });
    }
    revalidatePath("/scrape-runs");
    return {
      success: true,
      message: `Queued ${boards.length} boards — run "python3 scripts/run_once.py scrape" locally to execute.`,
    };
  }
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

export async function clearScrapedJobs() {
  // Delete in dependency order: outreach_messages → scraped_jobs → scrape_runs
  const deletedMessages = await prisma.outreach_messages.deleteMany({});
  const deletedJobs = await prisma.scraped_jobs.deleteMany({});
  const deletedRuns = await prisma.scrape_runs.deleteMany({});

  revalidatePath("/scrape-runs");
  revalidatePath("/outreach");
  revalidatePath("/");
  return {
    success: true,
    jobsDeleted: deletedJobs.count,
    runsDeleted: deletedRuns.count,
    messagesDeleted: deletedMessages.count,
  };
}
