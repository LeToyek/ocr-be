"use strict";

const express = require("express");
const http = require("http");
const morgan = require("morgan");
const bodyParser = require("body-parser");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const helmet = require("helmet");
const path = require("path");
const fs = require("fs");
const dotenv = require("dotenv");
const moment = require("moment");
const csurf = require("csurf");
const response = require("./src/tools/response");

// dotenv.config({ path: path.join(__dirname, "./env/.env.dev") });

const app = express();

// Middleware for parsing JSON
app.use(express.json({ limit: process.env.JSON_REQUEST_LIMIT }));
// Middleware for parsing URL-encoded data
app.use(
  express.urlencoded({ limit: process.env.JSON_REQUEST_LIMIT, extended: true })
);

app.use(morgan("dev"));

// Security Middleware
app.use(
  helmet({
    crossOriginResourcePolicy: process.env.NODE_ENV === "production",
  })
);

// Enable cookie parsing
app.use(cookieParser("testing, ", { httpOnly: true }));

// CORS Configuration
const corsOptions = {
  origin: function (origin, callback) {
    // Check if the request should be allowed from the given origin
    // You can implement your own logic to validate the origin

    // Allow requests without a specified origin (e.g., Postman)
    const allowedOrigins = [
      "http://localhost:4200",
      "http://172.19.1.15",
      "http://inapps",
      "http://inapps.aio.co.id",
      "https://inapps.aio.co.id",
      'http://192.168.1.17:4200',
      'http://192.168.214.231:4200',
      'http://192.168.18.9:4200',
      'http://192.168.18.9',
      'https://lotno.molana.my.id'
    ];

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error("Not allowed by CORS"));
    }
  },
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: [
    "Content-Type",
    "Authorization",
    "X-XSRF-TOKEN",
    "X-Page-URL",
  ],
  credentials: true,
  optionsSuccessStatus: 204,
};

app.use(cors(corsOptions));

// Add static file serving before the routes
app.use('/public', express.static(path.join(__dirname, 'public')));

// Routes registration
const routesDir = path.join(__dirname, "./src/routes");
fs.readdirSync(routesDir).forEach((file) => {
  const routePath = path.join(routesDir, file);
  const routePathWithoutExt = path.parse(routePath).name;

  const dashedRoutePath = routePathWithoutExt
    .replace(/([a-zA-Z])(?=[A-Z])/g, "$1-")
    .toLowerCase();

  app.use(`/api/${dashedRoutePath}`, require(routePath));
});

// Enable CSRF protection
const csrfProtection = csurf({ cookie: true });
app.use(csrfProtection);

app.get("/api/csrf-token", (req, res) => {
  // res.cookie('XSRF-TOKEN', req.csrfToken());
  const csrfToken = req.csrfToken();
  res.cookie("XSRF-TOKEN", csrfToken);
  response(req, res, {
    status: 200,
    data: csrfToken,
    message: "Success",
  });
});

// Error handler
app.use((err, req, res, next) => {
  response(req, res, {
    status: err.status || 500,
    message: err.message || "Internal Server Error",
  });
});

// Start the server
const port = process.env.PORT || 3000;
app.set("port", port);

const server = http.createServer(app);
// server.listen(port,'0.0.0.0');
server.listen(port,'0.0.0.0');
server.on("error", onError);
server.on("listening", onListening);

function onError(error) {
  if (error.syscall !== "listen") {
    throw error;
  }

  const bind = typeof port === "string" ? "Pipe " + port : "Port " + port;

  switch (error.code) {
    case "EACCES":
      console.error(bind + " requires elevated privileges");
      process.exit(1);
      break;
    case "EADDRINUSE":
      console.error(bind + " is already in use");
      process.exit(1);
      break;
    default:
      throw error;
  }
}

function onListening() {
  const addr = server.address();
  const bind = typeof addr === "string" ? "pipe " + addr : "port " + addr.port;

  console.log(
    `[OK] ${process.env.SERVICE_NAME} running on port: ${process.env.PORT}`
  );
}

// ======================= SCHEDULER SECTION END ===============================
