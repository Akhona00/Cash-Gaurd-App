const { PythonShell } = require("python-shell");

let options = {
  mode: "text", // Set the mode to "text" (default is "json")
  pythonPath: "python", // Specify the path to your Python interpreter (e.g., "python3" or "python")
  scriptPath: ".", // Set the path to the directory containing your Python script
  args: ["winter", "jane"], // Arguments to pass to the Python script
};

PythonShell.run("py-script.py", options, function (err, results) {
  if (err) {
    console.error("Error running Python script:", err);
  } else {
    console.log(results);
    console.log("Python script finished");
  }
});
