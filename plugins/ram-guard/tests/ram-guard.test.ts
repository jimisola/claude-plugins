import { describe, expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'

import { countJobs, parseGtt, parseMeminfo, refuseAgent, refuseCommand, statusLine } from '../hooks/scan'

const GiB = 1024 * 1024
const meminfo = (availableGiB: number) =>
  `MemTotal:       ${28 * GiB} kB\nMemFree:        1000 kB\nMemAvailable:   ${availableGiB * GiB} kB\n`

const GRADLE = 'java -cp gradle-launcher.jar org.gradle.launcher.daemon.bootstrap.GradleDaemon 8.10'
const MAVEN = 'java -classpath .mvn/wrapper org.codehaus.plexus.classworlds.launcher.Launcher clean verify'
const OLLAMA_RUNNER = '/usr/local/bin/ollama runner --model /usr/share/ollama/.ollama/models/blobs/sha256-60e0 --port 37707'
const quiet = { availableGiB: 20, totalGiB: 28, igpuGiB: 0, jobs: countJobs('') }

describe('scan', () => {
  test('reads MemAvailable and MemTotal in GiB', () => {
    expect(parseMeminfo(meminfo(12))).toEqual({ availableGiB: 12, totalGiB: 28 })
  })

  test('counts each heavy job by its command line', () => {
    expect(countJobs(`${GRADLE}\n${GRADLE}\n${MAVEN}\n/opt/android/emulator/qemu/linux-x86_64/qemu-system-x86_64 -avd p\nbash`))
      .toEqual({ gradle: 2, emulator: 1, maven: 1, metro: 0, ollama: 0 })
  })

  test('counts an Expo dev server once, not once per launcher', () => {
    const chain = [
      "/bin/bash -c pnpm exec expo start --port 8081",
      'node /usr/bin/pnpm exec expo start --port 8081',
      '/cache/pnpm-native exec expo start --port 8081',
      'node /app/node_modules/.bin/../expo/bin/cli start --port 8081',
    ].join('\n')
    expect(countJobs(chain).metro).toBe(1)
  })

  test('counts a loaded Ollama model by its runner, not the idle server', () => {
    const ps = ['/usr/local/bin/ollama serve', 'ollama pull gemma3:4b', OLLAMA_RUNNER].join('\n')
    expect(countJobs(ps).ollama).toBe(1)
    expect(countJobs('/usr/local/bin/ollama serve').ollama).toBe(0)
  })

  test('sums iGPU GTT bytes across cards and shows it once it reaches 1 GiB', () => {
    expect(parseGtt(`${5 * 1024 ** 3}\n${1024 ** 3}\n`)).toBe(6)
    expect(parseGtt('')).toBe(0)
    expect(statusLine({ ...quiet, igpuGiB: 5.3, jobs: countJobs(OLLAMA_RUNNER) })).toBe('RAM 20.0/28G free · ollama 1 · igpu 5.3G')
    expect(statusLine({ ...quiet, igpuGiB: 0.2 })).toBe('RAM 20.0/28G free')
  })

  test('a loaded model does not block a subagent; only the memory floor does', () => {
    expect(refuseAgent({ ...quiet, jobs: countJobs(OLLAMA_RUNNER) })).toBeUndefined()
  })

  test('a subagent waits for a Gradle daemon and for low memory, not for another subagent', () => {
    expect(refuseAgent(quiet)).toBeUndefined()
    expect(refuseAgent({ ...quiet, jobs: countJobs(GRADLE) })).toContain('Gradle daemon')
    expect(refuseAgent({ ...quiet, availableGiB: 5 })).toContain('under the 6 GiB')
  })

  test('only a heavy command is refused, and only under the build floor', () => {
    expect(refuseCommand({ ...quiet, availableGiB: 3 }, './mvnw clean verify')).toContain('under the 4 GiB')
    expect(refuseCommand({ ...quiet, availableGiB: 3 }, 'git status')).toBeUndefined()
    expect(refuseCommand({ ...quiet, availableGiB: 5 }, './gradlew build')).toBeUndefined()
    expect(refuseCommand({ ...quiet, availableGiB: 3 }, 'ollama run qwen2.5-coder:7b')).toContain('under the 4 GiB')
    expect(refuseCommand({ ...quiet, availableGiB: 3 }, 'ollama list')).toBeUndefined()
  })
})

function host(on: On, availableGiB: number, ps: () => string = () => '') {
  on('fs.read', () => ({ value: meminfo(availableGiB) }))
  on('process.run', (_, e) => ({
    value: { exitCode: 0, stdout: e.argv[0] === 'ps' ? ps() : '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false },
  }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.toast', () => ({ value: undefined }))
}

describe('register', () => {
  test('refuses a subagent beside a Gradle daemon and lets it start once the daemon is gone', async ($, on) => {
    let ps = GRADLE
    host(on, 20, () => ps)
    on('tool.call', () => ({ result: { status: 'async_launched' } }))

    const beside = await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'y' })
    expect(beside.deny).toContain('Gradle daemon')

    ps = ''
    const alone = await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'y' })
    expect(alone.deny).toBeUndefined()
  })

  test('refuses a build under the floor and lets other commands through', async ($, on) => {
    host(on, 2, () => MAVEN)
    on('tool.call', () => ({ result: { stdout: '', stderr: '', interrupted: false } }))

    const build = await $.tool.call({ tool: 'Bash', command: './mvnw clean verify' })
    expect(build.deny).toContain('under the 4 GiB')

    const status = await $.tool.call({ tool: 'Bash', command: 'git status' })
    expect(status.deny).toBeUndefined()
  })
})
