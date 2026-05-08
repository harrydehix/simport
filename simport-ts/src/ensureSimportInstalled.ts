import { exec, spawn } from "child_process";
import { promisify } from "util";
import * as os from "os";
import * as path from "path";
import * as fs from "fs";

const execAsync = promisify(exec);

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

export async function ensureSimportInstalled(
    installScriptPathOrUrl: string,
    vibesIntegration = false,
): Promise<void> {
    const isInstalled = await isCommandAvailable("simport");

    if (isInstalled) {
        console.log("simport is already installed and available in PATH.");
        return;
    }

    console.log("simport is not installed. Preparing installation...");

    let pythonScriptToRun = installScriptPathOrUrl;
    let isTempFile = false;

    if (
        installScriptPathOrUrl.startsWith("http://") ||
        installScriptPathOrUrl.startsWith("https://")
    ) {
        console.log(
            `
            Downloading install script from ${installScriptPathOrUrl}...`,
        );
        const response = await fetch(installScriptPathOrUrl);
        if (!response.ok) {
            throw new Error(
                `Failed to download install script: ${response.statusText}`,
            );
        }
        const text = await response.text();
        pythonScriptToRun = path.join(os.tmpdir(), "install_simport.py");
        fs.writeFileSync(pythonScriptToRun, text, "utf-8");
        isTempFile = true;
    }

    return new Promise((resolve, reject) => {
        const args = [pythonScriptToRun];
        if (vibesIntegration) {
            args.push("--vibes-integration");
        }
        const child = spawn("python", args, {
            stdio: "inherit",
            shell: true,
        });

        child.on("close", (code) => {
            if (isTempFile && fs.existsSync(pythonScriptToRun)) {
                fs.unlinkSync(pythonScriptToRun);
            }
            if (code === 0) {
                console.log("simport installation completed successfully.");
                resolve();
            } else {
                reject(new Error(`Installation failed with exit code ${code}`));
            }
        });

        child.on("error", (err) => {
            if (isTempFile && fs.existsSync(pythonScriptToRun)) {
                fs.unlinkSync(pythonScriptToRun);
            }
            reject(
                new Error(
                    `Failed to start installation process: ${err.message}`,
                ),
            );
        });
    });
}
