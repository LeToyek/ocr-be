/**
 * Usage example:
 * 
 * npm run models-dev -- --db=example table1 table2
 * 
 * db: Select from available database configurations (e.g., example)
 * table1 table2: Optional list of specific tables to generate models for
 */

const path = require("path");
const SequelizeAuto = require('sequelize-auto');
const dotenv = require("dotenv");

// Load environment variables
dotenv.config({path: path.join(__dirname, "../env/.env.dev")});

console.log("env example user ", process.env.MYSQL_EXAMPLE_USER);

// Function to convert names to camelCase
const toCamelCaseName = (str) => {
  return str
    .toLowerCase()
    .replace(/_(.)/g, (_, match) => match.toUpperCase());
};

// Initialize SequelizeAuto for MySQL
const auto = new SequelizeAuto(
  process.env.MYSQL_EXAMPLE_NAME,
  process.env.MYSQL_EXAMPLE_USER,
  process.env.MYSQL_EXAMPLE_PASS,
  {
    host: process.env.MYSQL_EXAMPLE_HOST,
    dialect: process.env.MYSQL_EXAMPLE_DIALECT,
    port: process.env.MYSQL_EXAMPLE_PORT,
    directory: path.join(__dirname, `../src/models/${toCamelCaseName(process.env.MYSQL_EXAMPLE_NAME)}`),
    additional: {
      timestamps: false,
      underscored: true,
    },
  }
);

// Generate models
auto.run((err) => {
  if (err) throw err;
  console.log('Models generated successfully!');
});
