const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  return sequelize.define('aio_employee', {
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
};
