const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  // Define the model
  const aio_employee = sequelize.define('aio_employee', {
    lg_nik: {
      type: DataTypes.STRING(255),
      allowNull: false,
      primaryKey: true
    },
    lg_password: {
      type: DataTypes.STRING(255),
      allowNull: true
    },
    lg_name: {
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
    tableName: 'aio_employee',
    timestamps: false,
    underscored: true,
    indexes: [
      {
        name: "PRIMARY",
        unique: true,
        using: "BTREE",
        fields: [
          { name: "lg_nik" },
        ]
      },
    ]
  });

  // Add the associate method
  aio_employee.associate = function(models) {
    // AioEmployee has many OcrResults
    aio_employee.hasMany(models.ocr_results, {
      foreignKey: 'employee_id', // The foreign key in the ocr_results table
      sourceKey: 'lg_nik', // Specify the source key in this table
      as: 'ocr_results' // Alias for the association
    });
  };

  return aio_employee; // Return the defined model
};
