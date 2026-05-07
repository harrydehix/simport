import { exec } from "child_process";
import { promisify } from "util";
import * as os from "os";
import * as path from "path";
import * as fs from "fs";
import { fileURLToPath } from "url";

const execAsync = promisify(exec);

/**
 * Checks if a specific command is available in the system PATH.
 */
async function isCommandAvailable(command: string): Promise<boolean> {
    const checkCmd =
        os.platform() === "win32"
            ? `where ${command}`
            : `command -v ${command}`;
    try {
        await execAsync(checkCmd);
        return true;
    } catch {
        return false;
    }
}

/**
 * Checks if the currently installed ffmpeg is version 7.x and (on Windows) is a shared build.
 */
async function checkValidFfmpeg(userDataPath?: string): Promise<{
    valid: boolean;
    currentVersion?: string;
    reason?: string;
}> {
    try {
        let ffmpegCmd = "ffmpeg";
        const home = os.homedir();
        if (
            os.platform() === "win32" &&
            (userDataPath || process.env.APPDATA)
        ) {
            const ffmpegExe = userDataPath
                ? path.join(userDataPath, "ffmpeg", "bin", "ffmpeg.exe")
                : path.join(
                      process.env.APPDATA!,
                      "vibes",
                      "ffmpeg",
                      "bin",
                      "ffmpeg.exe",
                  );
            ffmpegCmd = `"${ffmpegExe}"`;
        } else if (os.platform() === "darwin") {
            const ffmpegExe = userDataPath
                ? path.join(userDataPath, "ffmpeg", "bin", "ffmpeg")
                : path.join(
                      home,
                      "Library",
                      "Application Support",
                      "vibes",
                      "ffmpeg",
                      "bin",
                      "ffmpeg",
                  );
            ffmpegCmd = `"${ffmpegExe}"`;
        }

        const { stdout } = await execAsync(`${ffmpegCmd} -version`);
        // Extract version, e.g., "ffmpeg version 7.0.2-essentials_build-www.gyan.dev ..." or "ffmpeg version n7.0"
        const versionMatch = stdout.match(
            /ffmpeg version [a-zA-Z]*(\d+\.\d+(\.\d+)?)/,
        );
        const currentVersion = versionMatch ? versionMatch[1] : "unknown";

        if (!currentVersion.startsWith("7.")) {
            return {
                valid: false,
                currentVersion,
                reason: `requires v7.x, but found v${currentVersion}`,
            };
        }

        if (os.platform() === "win32" && !stdout.includes("--enable-shared")) {
            return {
                valid: false,
                currentVersion,
                reason: `found v${currentVersion}, but it is not a shared build (--enable-shared missing)`,
            };
        }

        return { valid: true, currentVersion };
    } catch {
        return {
            valid: false,
            reason: "Command not found or execution failed",
        };
    }
}

/**
 * Tries to install ffmpeg based on the operating system.
 */
async function ensureFfmpeg(userDataPath?: string): Promise<void> {
    const ffmpegCheck = await checkValidFfmpeg(userDataPath);
    if (ffmpegCheck.valid) {
        console.log(
            `✅ ffmpeg (v${ffmpegCheck.currentVersion}) is already installed and valid.`,
        );
        return;
    }

    console.log(
        `🔄 ffmpeg validation failed (${ffmpegCheck.reason}). Attempting to install proper v7...`,
    );
    const platform = os.platform();

    try {
        if (platform === "win32") {
            const appData = userDataPath || process.env.APPDATA;
            if (!appData)
                throw new Error("APPDATA environment variable not found");

            const ffmpegBaseDir = path.join(appData, "ffmpeg");
            const tempZip = path.join(os.tmpdir(), "ffmpeg.zip");

            console.log(
                `Downloading Portable FFmpeg (v7.1.1 Shared) to ${tempZip}...`,
            );
            await execAsync(
                `powershell -ExecutionPolicy ByPass -c "Invoke-WebRequest -Uri 'https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-full_build-shared.zip' -OutFile '${tempZip}'"`,
            );

            console.log(`Extracting FFmpeg to ${ffmpegBaseDir}...`);
            await execAsync(
                `powershell -ExecutionPolicy ByPass -c "Expand-Archive -Path '${tempZip}' -DestinationPath '${appData}\\ffmpeg_temp' -Force"`,
            );

            // Move extracted subfolder to target dir
            await execAsync(
                `powershell -ExecutionPolicy ByPass -c "if (Test-Path '${ffmpegBaseDir}') { Remove-Item -Recurse -Force '${ffmpegBaseDir}' }; Rename-Item -Path '${appData}\\ffmpeg_temp\\ffmpeg-7.1.1-full_build-shared' -NewName 'ffmpeg'; Move-Item -Path '${appData}\\ffmpeg_temp\\ffmpeg' -Destination '${appData}'; Remove-Item -Recurse -Force '${appData}\\ffmpeg_temp'; Remove-Item -Force '${tempZip}'"`,
            );

            console.log(`✅ portable ffmpeg installed to ${ffmpegBaseDir}`);
        } else if (platform === "darwin") {
            const home = os.homedir();
            const ffmpegBaseDir = userDataPath
                ? path.join(userDataPath, "ffmpeg")
                : path.join(
                      home,
                      "Library",
                      "Application Support",
                      "vibes",
                      "ffmpeg",
                  );
            const tempZip = path.join(os.tmpdir(), "ffmpeg-mac.zip");

            console.log(
                `Downloading static ffmpeg (v7.1.1) for macOS to ${tempZip}...`,
            );
            await execAsync(
                `curl -L https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip -o "${tempZip}"`,
            );

            console.log(`Extracting ffmpeg to ${ffmpegBaseDir}/bin...`);
            await execAsync(`mkdir -p "${ffmpegBaseDir}/bin"`);
            await execAsync(`unzip -o "${tempZip}" -d "${ffmpegBaseDir}/bin"`);
            await execAsync(`rm "${tempZip}"`);

            console.log(`✅ portable ffmpeg installed to ${ffmpegBaseDir}`);
        } else if (platform === "linux") {
            // Note: This might require password input or fail if not run as root.
            console.log(
                "⚠️ On Linux, trying to install ffmpeg via apt-get which might require root privileges.",
            );
            await execAsync(
                "sudo apt-get update && sudo apt-get install -y ffmpeg",
            );
        } else {
            throw new Error(
                `Unsupported OS for automatic ffmpeg installation: ${platform}`,
            );
        }
        console.log("✅ ffmpeg installed successfully.");
    } catch (error) {
        throw new Error(
            `❌ Failed to install ffmpeg automatically. Please install it manually and ensure it is in your PATH. Error: ${error instanceof Error ? error.message : error}`,
        );
    }
}

/**
 * Tries to install the Astral 'uv' package manager.
 */
async function ensureUv(): Promise<void> {
    if (await isCommandAvailable("uv")) {
        console.log("✅ uv is already installed.");
        return;
    }

    console.log("🔄 uv not found. Attempting to install...");
    const platform = os.platform();

    try {
        if (platform === "win32") {
            await execAsync(
                'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
            );
        } else {
            await execAsync("curl -LsSf https://astral.sh/uv/install.sh | sh");
        }

        // On Unix, we might need to add it to the path for the current process temporarily
        if (platform !== "win32" && process.env.HOME) {
            process.env.PATH = `${process.env.HOME}/.local/bin:${process.env.PATH}`;
        }
        if (platform === "win32" && process.env.USERPROFILE) {
            process.env.PATH = `${process.env.USERPROFILE}\\.cargo\\bin;${process.env.PATH}`;
        }
        console.log("✅ uv installed successfully.");
    } catch (error) {
        throw new Error(
            `❌ Failed to install uv automatically. Error: ${error instanceof Error ? error.message : error}`,
        );
    }
}

/**
 * Checks if an NVIDIA GPU (CUDA) is available by testing nvidia-smi.
 */
async function hasCuda(): Promise<boolean> {
    try {
        await execAsync("nvidia-smi");
        return true;
    } catch {
        return false;
    }
}

/**
 * Installs PyTorch using 'uv pip' with the correct index-url based on OS and CUDA availability.
 */
async function ensurePyTorch(projectRoot: string): Promise<void> {
    console.log("🔄 Checking PyTorch requirements...");
    const platform = os.platform();
    let installCmd =
        'uv pip install "torch~=2.6.0" "torchvision~=0.21.0" "torchaudio~=2.6.0"';

    if (platform === "darwin") {
        // Mac: Always Default / Pip
        console.log(
            "🍎 Detected macOS. Using default PyTorch build (MPS supported natively).",
        );
    } else {
        const cudaAvailable = await hasCuda();
        if (cudaAvailable) {
            console.log(
                "🟩 Detected NVIDIA GPU. Installing PyTorch with CUDA 12.6 support...",
            );
            installCmd += " --index-url https://download.pytorch.org/whl/cu126";
        } else {
            console.log(
                "⬜ No NVIDIA GPU detected. Installing PyTorch with CPU support...",
            );
            if (platform === "linux") {
                installCmd +=
                    " --index-url https://download.pytorch.org/whl/cpu";
            }
            // For Windows CPU, the default command (without index-url) is correct for pip/uv
        }
    }

    try {
        // Ensure a virtual environment exists
        await execAsync("uv sync", { cwd: projectRoot });
        console.log("✅ UV dependencies installed successfully.");
        await execAsync(installCmd + " --reinstall", { cwd: projectRoot });
        console.log("✅ PyTorch installed successfully.");
    } catch (error) {
        throw new Error(
            `❌ Failed to install PyTorch automatically. Error: ${error instanceof Error ? error.message : error}`,
        );
    }
}

/**
 * Ensures that simport is installed and ready to use.
 * This function handles its prerequisites (ffmpeg, uv, PyTorch) and registers the CLI tool.
 *
 * @param projectRoot The root directory for the simport project.
 * @param forceReinstall Whether to force a reinstall of the dependencies.
 */
export async function ensureSimportInstalled(
    projectRoot?: string,
    forceReinstall = false,
): Promise<void> {
    if (!projectRoot) {
        const home = os.homedir();
        if (os.platform() === "win32" && process.env.APPDATA) {
            projectRoot = path.join(process.env.APPDATA, "vibes", "simport");
        } else if (os.platform() === "darwin") {
            projectRoot = path.join(
                home,
                "Library",
                "Application Support",
                "vibes",
                "simport",
            );
        } else {
            projectRoot = path.join(
                home,
                ".local",
                "share",
                "vibes",
                "simport",
            );
        }
    }

    console.log(
        `🚀 Starting simport installation process in ${path.resolve(projectRoot)}...`,
    );

    try {
        // 0. Download source if missing (check for pyproject.toml as an indicator)
        if (!fs.existsSync(path.join(projectRoot, "pyproject.toml"))) {
            console.log(`🔄 Downloading simport source to ${projectRoot}...`);
            const platform = os.platform();
            const zipUrl =
                "https://github.com/harrydehix/vibes-ai-based-import/archive/refs/heads/main.zip";
            const tempZip = path.join(os.tmpdir(), "simport-src.zip");

            if (platform === "win32") {
                await execAsync(
                    `powershell -ExecutionPolicy ByPass -c "Invoke-WebRequest -Uri '${zipUrl}' -OutFile '${tempZip}'"`,
                );
                const tempExtract = path.join(os.tmpdir(), "simport_extract");
                await execAsync(
                    `powershell -ExecutionPolicy ByPass -c "if (Test-Path '${tempExtract}') { Remove-Item -Recurse -Force '${tempExtract}' }; Expand-Archive -Path '${tempZip}' -DestinationPath '${tempExtract}' -Force"`,
                );
                await execAsync(
                    `powershell -ExecutionPolicy ByPass -c "if (-not (Test-Path '${projectRoot}')) { New-Item -ItemType Directory -Force -Path '${projectRoot}' }; Move-Item -Path '${tempExtract}\\vibes-ai-based-import-main\\*' -Destination '${projectRoot}' -Force; Remove-Item -Recurse -Force '${tempExtract}'; Remove-Item -Force '${tempZip}'"`,
                );
            } else {
                await execAsync(`curl -L "${zipUrl}" -o "${tempZip}"`);
                await execAsync(`mkdir -p "${projectRoot}"`);
                const tempExtract = path.join(os.tmpdir(), "simport_extract");
                await execAsync(
                    `rm -rf "${tempExtract}" && mkdir -p "${tempExtract}"`,
                );
                await execAsync(`unzip -o "${tempZip}" -d "${tempExtract}"`);
                await execAsync(
                    `cp -a "${tempExtract}"/vibes-ai-based-import-main/. "${projectRoot}/"`,
                );
                await execAsync(`rm -rf "${tempExtract}" "${tempZip}"`);
            }
            console.log("✅ simport source downloaded and extracted.");
        }

        // 1. Ensure prerequisites
        await ensureFfmpeg(path.join(projectRoot, ".."));
        await ensureUv();

        // 2. Check if simport is already installed via uv
        if ((await isCommandAvailable("simport")) && !forceReinstall) {
            console.log("✅ simport CLI is already installed.");
            // Optionally run an update here, e.g., uv tool upgrade simport
            return;
        }
        console.log("🔄 Installing simport via uv tool...");

        // 3. Install the tool using uv in editable mode

        let installCmd = `uv tool install --python 3.12 --editable .`;

        // Ensure CUDA passes through to the tool installation environment!
        const platform = os.platform();
        if (platform === "win32" && (await hasCuda())) {
            installCmd +=
                " --extra-index-url https://download.pytorch.org/whl/cu126 --index-strategy unsafe-best-match";
        } else if (platform === "linux" && !(await hasCuda())) {
            installCmd +=
                " --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match";
        }

        if (forceReinstall) {
            installCmd += " --reinstall";
        }

        const { stdout, stderr } = await execAsync(installCmd, {
            cwd: projectRoot, // The directory containing pyproject.toml
        });

        if (stderr && !stderr.includes("Successfully installed")) {
            console.warn(`⚠️ Warning during uv installation: ${stderr}`);
        }

        // Ensure pyproject is synced and PyTorch applies correctly
        await ensurePyTorch(projectRoot);

        console.log(
            "✅ simport installed successfully. You can now use the simport CLI!",
        );
    } catch (error) {
        console.error("❌ Error during simport installation:", error);
        throw error;
    }
}
