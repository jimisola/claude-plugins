import type { EngineInterface, Register } from 'claude-code'

import { AGENT_FLOOR_GIB, countJobs, parseGtt, parseMeminfo, refuseAgent, refuseCommand, statusLine } from './scan'
import type { Snapshot } from './scan'

async function snapshot($: EngineInterface): Promise<Snapshot> {
  const [meminfo, ps, gtt] = await Promise.all([
    $.fs.read('/proc/meminfo'),
    $.process.run(['ps', '-eo', 'args=']),
    // No amdgpu card means no match and empty output, which reads as 0.
    $.process.run(['sh', '-c', 'cat /sys/class/drm/card*/device/mem_info_gtt_used 2>/dev/null']),
  ])

  return { ...parseMeminfo(meminfo), igpuGiB: parseGtt(gtt.stdout), jobs: countJobs(ps.stdout) }
}

// Edge-triggers the low-memory toast; a reload starting it over costs at most one repeat.
let wasLow = false

async function refresh($: EngineInterface): Promise<Snapshot> {
  const s = await snapshot($)
  $.ui.status(statusLine(s))
  const isLow = s.availableGiB < AGENT_FLOOR_GIB
  if (isLow && !wasLow) {
    $.ui.toast(`RAM low: ${s.availableGiB.toFixed(1)} GiB available`)
  }
  wasLow = isLow

  return s
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await refresh($)
    $.clock.every(15_000, () => refresh($))

    return started
  })

  on('tool.call', { tool: ['Agent', 'Workflow'] }, async ($, e, next) => {
    const why = refuseAgent(await refresh($))

    return why ? { deny: `ram-guard: ${why}.` } : next(e)
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const why = refuseCommand(await refresh($), e.command)

    return why ? { deny: `ram-guard: ${why}.` } : next(e)
  })
}
