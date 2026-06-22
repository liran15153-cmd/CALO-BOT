import { spawnSync } from 'node:child_process';

function run(command, args) {
  const result =
    process.platform === 'win32'
      ? spawnSync([command, ...args].join(' '), { shell: true, stdio: 'inherit' })
      : spawnSync(command, args, { stdio: 'inherit' });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run('python', ['scripts/secret_scan.py']);
run('python', ['-m', 'pytest', 'backend/tests', '--basetemp=.pytest-tmp']);
run('npm', ['--prefix', 'frontend', 'test', '--', '--run']);
