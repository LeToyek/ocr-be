var DataTypes = require("sequelize").DataTypes;
var _ocr_results = require("./ocr_results");
var _users = require("./users");

function initModels(sequelize) {
  var ocr_results = _ocr_results(sequelize, DataTypes);
  var users = _users(sequelize, DataTypes);

  ocr_results.belongsTo(users, { as: "user", foreignKey: "user_id"});
  users.hasMany(ocr_results, { as: "ocr_results", foreignKey: "user_id"});

  return {
    ocr_results,
    users,
  };
}
module.exports = initModels;
module.exports.initModels = initModels;
module.exports.default = initModels;
