const { spawn } = require('child_process');
const path = require("path");
const os = require('os');  // Import the os module


const runCommand = (args) => {
    return new Promise((resolve, reject) => {
        const isWindows = os.platform() === 'win32'; // Detect if the OS is Windows
        const venvPath = path.resolve(__dirname, '../python/venv');
        const pythonExecutable = isWindows
            ? path.join(venvPath, 'Scripts', 'python.exe')  // Windows path
            : path.join(venvPath, 'bin', 'python');         // Linux/Mac path

        console.log(`Executing command: ${pythonExecutable} ${args.join(" ")}`); // Log the command to see the actual path being used

        const process = spawn(pythonExecutable, args);

        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        process.on('close', (code) => {
            if (code !== 0) {
                console.error(`Process exited with code ${code}`);
                console.error(`stderr: ${stderr}`);
                return reject(new Error(stderr));
            }

            console.log(`stdout: ${stdout}`);
            resolve(stdout);
        });
    });
};

module.exports = runCommand;
