# Safe Code Runner Policy

The safe code runner is disabled by default through `SAFE_CODE_RUNNER_ENABLED=false`.

It may only become active after an approved isolation backend passes a capability check. Future options may include an operating-system sandbox, restricted subprocess backend, WebAssembly runtime, or dedicated isolated remote runner.

The runner must not access repository secrets, home directories, environment secrets, production MongoDB credentials, SSH keys, Git credentials, local model files, unrelated paths, or network access by default.
