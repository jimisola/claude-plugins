// Pure parsing and policy, kept apart from register.ts so tests need no host.

export type Job = 'gradle' | 'emulator' | 'maven' | 'metro' | 'ollama'

export type Snapshot = {
  availableGiB: number
  totalGiB: number
  // System RAM the iGPU has borrowed (amdgpu GTT); a loaded model lives here, not in its RSS.
  igpuGiB: number
  jobs: Record<Job, number>
}

// Below this, no subagent starts.
export const AGENT_FLOOR_GIB = 6
// Below this, no heavy build starts either.
export const BUILD_FLOOR_GIB = 4

const JOBS: readonly [Job, RegExp][] = [
  ['gradle', /org\.gradle\.launcher\.daemon\.bootstrap\.GradleDaemon/],
  ['emulator', /qemu-system-|\/emulator\/emulator\b/],
  ['maven', /org\.codehaus\.plexus\.classworlds\.launcher\.Launcher/],
  // Anchored on the node process itself: its bash -c and pnpm exec launchers repeat the command line.
  ['metro', /^node\s\S*(expo\/bin\/cli|react-native\/cli\.js|metro\/src\/cli)\S*\sstart\b/],
  // One runner per loaded model; `ollama serve` alone holds no model.
  ['ollama', /^\S*\bollama runner\s/],
]

// Commands that start one of the jobs above, or a build as heavy.
const HEAVY = /\b(gradlew|mvnw|mvn)\b|\bemulator\s+-avd\b|\bpnpm\s+(e2e|test:stories)\b|\bollama\s+run\b/

const GIB = 1024 * 1024

export function parseMeminfo(text: string): { availableGiB: number; totalGiB: number } {
  const kib = (key: string) => Number(new RegExp(`^${key}:\\s+(\\d+)`, 'm').exec(text)?.[1] ?? 0)

  return { availableGiB: kib('MemAvailable') / GIB, totalGiB: kib('MemTotal') / GIB }
}

export function countJobs(psArgs: string): Record<Job, number> {
  const jobs: Record<Job, number> = { gradle: 0, emulator: 0, maven: 0, metro: 0, ollama: 0 }
  for (const line of psArgs.split('\n')) {
    const hit = JOBS.find(([, pattern]) => pattern.test(line))
    if (hit) {
      jobs[hit[0]] += 1
    }
  }

  return jobs
}

/** Sums the GTT byte counts of every amdgpu card, one number per line, in GiB. */
export function parseGtt(text: string): number {
  return text.split('\n').reduce((sum, line) => sum + (Number(line) || 0), 0) / (GIB * 1024)
}

export function statusLine(s: Snapshot): string {
  const running = (Object.entries(s.jobs) as [Job, number][])
    .filter(([, n]) => n > 0)
    .map(([job, n]) => `${job} ${n}`)

  const igpu = s.igpuGiB >= 1 ? [`igpu ${s.igpuGiB.toFixed(1)}G`] : []

  return [`RAM ${s.availableGiB.toFixed(1)}/${Math.round(s.totalGiB)}G free`, ...running, ...igpu].join(' · ')
}

/** Why a subagent may not start now, or undefined when it may. */
export function refuseAgent(s: Snapshot): string | undefined {
  if (s.jobs.gradle > 0 || s.jobs.emulator > 0) {
    return `a ${s.jobs.gradle > 0 ? 'Gradle daemon' : 'emulator'} is up; never run a subagent beside one (stop only your own: ./gradlew --stop, adb emu kill)`
  }
  if (s.availableGiB < AGENT_FLOOR_GIB) {
    return `only ${s.availableGiB.toFixed(1)} GiB available, under the ${AGENT_FLOOR_GIB} GiB a subagent needs here`
  }

  return undefined
}

/** Why a heavy command may not start now, or undefined when it may. */
export function refuseCommand(s: Snapshot, command: string): string | undefined {
  if (!HEAVY.test(command) || s.availableGiB >= BUILD_FLOOR_GIB) {
    return undefined
  }

  return `only ${s.availableGiB.toFixed(1)} GiB available, under the ${BUILD_FLOOR_GIB} GiB a build needs here; free memory first (other sessions share this machine)`
}
