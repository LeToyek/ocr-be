const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  // Define the model
  const ocr_results = sequelize.define('ocr_results', {
    id: {
      autoIncrement: true,
      type: DataTypes.INTEGER,
      allowNull: false,
      primaryKey: true
    },
    employee_id: {
      type: DataTypes.STRING(255), // Ensure this matches aio_employee primary key type
      allowNull: false, // Or true if optional
      references: {
        model: 'aio_employee',
        key: 'lg_nik' // Ensure this matches aio_employee primary key name
      }
    },
    product_batch_id: {
      type: DataTypes.INTEGER,
      allowNull: true, // Or true if optional
      references: {
        model: 'product_batch',
        key: 'id'
      }
    },
    status:{
      type: DataTypes.STRING(50),
      allowNull: true,
    },
    category:{
      type: DataTypes.STRING(50),
      allowNull: true,
    },
    top_text: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    bottom_text: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    
    photo_url: { // Type was INTEGER, likely should be STRING or TEXT
      type: DataTypes.STRING(255),
      allowNull: true
    },
    created_at: {
      type: DataTypes.DATE,
      allowNull: true
    },
    updated_at: {
      type: DataTypes.DATE,
      allowNull: true
    }
  }, {
    sequelize,
    tableName: 'ocr_results',
    timestamps: false, // Set true if you want Sequelize to manage created_at/updated_at
    underscored: true,
    indexes: [
      {
        name: "PRIMARY",
        unique: true,
        using: "BTREE",
        fields: [
          { name: "id" },
        ]
      },
      {
        name: "employee_id",
        using: "BTREE",
        fields: [
          { name: "employee_id" },
        ]
      },
      {
        name: "product_batch_id",
        using: "BTREE",
        fields: [
          { name: "product_batch_id" },
        ]
      },
    ]
  });

  // Add the associate method
  ocr_results.associate = function(models) {
    // OcrResult belongs to an AioEmployee
    ocr_results.belongsTo(models.aio_employee, {
      foreignKey: 'employee_id', // The foreign key in this table
      targetKey: 'lg_nik', // Specify the target key in aio_employee
      as: 'employee' // Alias for the association
    });
    // OcrResult belongs to a ProductBatch
    ocr_results.belongsTo(models.product_batch, {
      foreignKey: 'product_batch_id', // The foreign key in this table
      as: 'product_batch' // Alias for the association
    });
  };

  return ocr_results; // Return the defined model
};
