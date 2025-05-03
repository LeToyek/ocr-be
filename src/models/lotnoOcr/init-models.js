var DataTypes = require("sequelize").DataTypes;
var _aio_employee = require("./aio_employee");
var _category = require("./category");
var _documents = require("./documents");
var _ocr_results = require("./ocr_results");
var _product_batch = require("./product_batch");

function initModels(sequelize) {
  var aio_employee = _aio_employee(sequelize, DataTypes);
  var category = _category(sequelize, DataTypes);
  var documents = _documents(sequelize, DataTypes);
  var ocr_results = _ocr_results(sequelize, DataTypes);
  var product_batch = _product_batch(sequelize, DataTypes);

  ocr_results.belongsTo(aio_employee, { as: "employee", foreignKey: "employee_id"});
  aio_employee.hasMany(ocr_results, { as: "ocr_results", foreignKey: "employee_id"});
  documents.belongsTo(category, { as: "category", foreignKey: "category_id"});
  category.hasMany(documents, { as: "documents", foreignKey: "category_id"});
  product_batch.belongsTo(documents, { as: "document", foreignKey: "document_id"});
  documents.hasMany(product_batch, { as: "product_batches", foreignKey: "document_id"});
  ocr_results.belongsTo(product_batch, { as: "product_batch", foreignKey: "product_batch_id"});
  product_batch.hasMany(ocr_results, { as: "ocr_results", foreignKey: "product_batch_id"});

  return {
    aio_employee,
    category,
    documents,
    ocr_results,
    product_batch,
  };
}
module.exports = initModels;
module.exports.initModels = initModels;
module.exports.default = initModels;
