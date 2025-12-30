const { app, session, shell, BrowserWindow, Menu } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const isMac = process.platform === "darwin";

let serverProcess;

async function createWindow(url) {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js"),
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
  win.setIcon(__dirname + "/icons/ausma.ai.png");
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
  if (fs.existsSync("flask_app/flask_app")) {
    // packaged with bundled python
    serverProcess = spawn("flask_app/flask_app", [
      "--production",
      "--localhost",
    ]);
  } else {
    // sets the path to include the virtual python environment
    const env = Object.assign({}, process.env);
    let parentDir = getParentDir();
    env["PATH"] = parentDir + "/backend/.venv/bin:" + env["PATH"];
    console.log(env["PATH"]);
    serverProcess = spawn(
      "python3",
      ["../backend/flask_app.py", "--production", "--localhost"],
      { env: env, cwd: parentDir + "/backend" }
    );
  }

  const is_loaded = new Promise((resolve, reject) => {
    serverProcess.stderr.on("data", function (data) {
      const dataStr = data.toString("utf8");
      if (dataStr.includes("Running on")) {
        resolve({});
      }
      process.stdout.write(dataStr);
    });
  });
  await is_loaded;
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
