pub mod analysis;
pub mod config;
pub mod fs_ops;
pub mod opentargets;
pub mod runtime;
pub mod setup;

/// Suppress the console window that flashes on Windows when spawning child processes.
/// No-op on non-Windows platforms.
pub(crate) fn hide_console(
    #[allow(unused_mut)] mut cmd: std::process::Command,
) -> std::process::Command {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    cmd
}
