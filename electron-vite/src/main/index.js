const { app, session, shell, BrowserWindow, Menu, ipcMain } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const isMac = process.platform === "darwin";

ipcMain.handle('show-item-in-folder', async (_, filePath) => {
  try {
    shell.showItemInFolder(filePath);

    return { success: true };
  } catch (err) {
    return {
      success: false,
      error: err.message,
    };
  }
});

let serverProcess;

async function createWindow(url) {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      preload: path.join(__dirname, path.join("..", "preload", "index.js")),
      additionalArguments: [`--defaultUsername=${os.userInfo().username}`],
    },
  });

  let contextMenu = Menu.buildFromTemplate([
    { role: "undo" },
    { role: "redo" },
    { type: "separator" },
    { role: "cut" },
    { role: "copy" },
    { role: "paste" },
    ...(isMac
      ? [
          { role: "pasteAndMatchStyle" },
          { role: "delete" },
          { role: "selectAll" },
          { type: "separator" },
          {
            label: "Speech",
            submenu: [{ role: "startSpeaking" }, { role: "stopSpeaking" }],
          },
        ]
      : [{ role: "delete" }, { type: "separator" }, { role: "selectAll" }]),
    { type: "separator" },
    {
      label: "Open in browser",
      click: async () => {
        await shell.openExternal(win.webContents.getURL());
      },
    },
  ]);

  win.setMenuBarVisibility(false);
  const iconPath = path.join(process.resourcesPath, 'icon.png');
  // Path differs if app is installed or run directly.
  if (fs.existsSync(iconPath)) {
    win.setIcon(iconPath);
  } else {
    win.setIcon(path.join(getParentDir(), "..", "resources", "icon.png"));
  }
  console.log(iconPath);
  win.loadURL(url);
  win.maximize();

  win.webContents.on("context-menu", (e) => {
    contextMenu.popup();
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    createWindow(url);
    return { action: "deny" };
  });

  win.show();
}

app.whenReady().then(async () => {
  if (app.commandLine.hasSwitch("dev")) {
    createWindow("http://localhost:5173");
  } else {
    await launchLocalServer();
    createWindow("http://localhost:5000");
  }
});

app.on("window-all-closed", () => {
  if (!isMac) app.quit();
});

async function launchLocalServer() {
  const packagedBackendPath = path.join(
    process.resourcesPath,
    'flask_app'
  )
  const packagedExecutablePath = path.join(
    packagedBackendPath,
    process.platform === 'win32' ? 'flask_app.exe' : 'flask_app'
  )
  const xpdfBinPath = process.platform === 'win32' ? path.join("windows", "pdftopng.exe") : path.join("linux", "pdftopng");
  if (fs.existsSync(packagedExecutablePath)) {
    // Python backend for installed electron app
    console.log('Running bundled python backend.\n');
    process.env['AUSMA_AI_DATA_PATH'] = path.join(app.getPath('userData'), 'ausma-ai');
    if (process.platform === 'win32') {
      process.env['PYTHONIOENCODING'] = 'utf-8'
    }
    process.env['XPDF_PATH'] = path.join(app.getPath('userData'), 'ausma-ai', "resources", "flask_app", "bin", xpdfBinPath);
    serverProcess = spawn(
      packagedExecutablePath,
      ["--production", "--localhost", "--frontend_path", path.join("..", "..", "frontend")],
      {'cwd': packagedBackendPath}
    );
  } else {
    // Python backend for unpacked electron app
    console.log('Running virtual environment python backend.\n')
    const env = Object.assign({}, process.env);
    let backendDir = path.join(getParentDir(), "..", "..", "backend");
    const backendVenvBinFolder = process.platform === "win32" ? "Scripts" : "bin";
    env["PATH"] = path.join(backendDir, ".venv", backendVenvBinFolder) + path.delimiter + env["PATH"];
    console.log(env["PATH"]);
    env["XPDF_PATH"] = path.join("bin", xpdfBinPath);
    serverProcess = spawn(
      process.platform === "win32" ? "python.exe" : "python3",
      [path.join(backendDir, "flask_app.py"), "--production", "--localhost", "--frontend_path", path.join("..", "frontend", "dist")],
      { env: env, cwd: backendDir }
    );
  }

  const isLoaded = new Promise((resolve, reject) => {
    serverProcess.stderr.on("data", function (data) {
      const dataStr = data.toString("utf8");
      if (dataStr.includes("Running on")) {
        resolve({});
      }
      process.stdout.write(dataStr);
    });
  });
  await isLoaded;
}

function getParentDir() {
  let parentDir = __dirname.split(path.sep);
  parentDir.pop();
  return parentDir.join(path.sep);
}

async function beforeQuit(e) {
  console.log("app stopping");
  if (serverProcess) {
    e.preventDefault();
    console.log("killing process");
    serverProcess.kill();
    serverProcess.on("exit", () => {
      console.log("exiting");
      serverProcess = null;
      app.quit();
    });
    console.log("waiting for process to stop");
  }
}

app.on("will-quit", beforeQuit);
