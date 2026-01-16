using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Resido.Migrations
{
    /// <inheritdoc />
    public partial class pincode : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "SmartLocks",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TTLockId = table.Column<int>(type: "integer", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Mac = table.Column<string>(type: "text", nullable: false),
                    AliasName = table.Column<string>(type: "text", nullable: true),
                    LockData = table.Column<string>(type: "text", nullable: true),
                    HasGateway = table.Column<int>(type: "integer", nullable: false),
                    FeatureValue = table.Column<string>(type: "text", nullable: true),
                    UserId = table.Column<Guid>(type: "uuid", nullable: false),
                    ElectricQuantity = table.Column<int>(type: "integer", nullable: false),
                    GroupId = table.Column<int>(type: "integer", nullable: false),
                    GroupName = table.Column<string>(type: "text", nullable: true),
                    IsNotificationOn = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    LastBatteryCheck = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SmartLocks", x => x.Id);
                    table.ForeignKey(
                        name: "FK_SmartLocks_Users_UserId",
                        column: x => x.UserId,
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AccessLogs",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    LockId = table.Column<int>(type: "integer", nullable: false),
                    LockMac = table.Column<string>(type: "text", nullable: true),
                    RecordType = table.Column<int>(type: "integer", nullable: false),
                    RecordTypeFromLock = table.Column<int>(type: "integer", nullable: false),
                    RecordTypeDescription = table.Column<string>(type: "text", nullable: true),
                    Username = table.Column<string>(type: "text", nullable: true),
                    KeyboardPwd = table.Column<string>(type: "text", nullable: true),
                    Success = table.Column<int>(type: "integer", nullable: false),
                    SmartLockId = table.Column<Guid>(type: "uuid", nullable: false),
                    BatteryPercentage = table.Column<int>(type: "integer", nullable: false),
                    IsAccessSuccessful = table.Column<bool>(type: "boolean", nullable: false),
                    LockEventLocalTime = table.Column<long>(type: "bigint", nullable: false),
                    ServerReceivedLocalTime = table.Column<long>(type: "bigint", nullable: false),
                    LockEventUtcTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    ServerReceivedUtcTime = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AccessLogs", x => x.Id);
                    table.ForeignKey(
                        name: "FK_AccessLogs_SmartLocks_SmartLockId",
                        column: x => x.SmartLockId,
                        principalTable: "SmartLocks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Card",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CardId = table.Column<int>(type: "integer", nullable: false),
                    CardNumber = table.Column<string>(type: "text", nullable: false),
                    SmartLockId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Card", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Card_SmartLocks_SmartLockId",
                        column: x => x.SmartLockId,
                        principalTable: "SmartLocks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "EKey",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    EKeyId = table.Column<int>(type: "integer", nullable: false),
                    KeyName = table.Column<string>(type: "text", nullable: false),
                    SmartLockId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EKey", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EKey_SmartLocks_SmartLockId",
                        column: x => x.SmartLockId,
                        principalTable: "SmartLocks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Fingerprint",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    FingerprintId = table.Column<int>(type: "integer", nullable: false),
                    FingerName = table.Column<string>(type: "text", nullable: false),
                    SmartLockId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Fingerprint", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Fingerprint_SmartLocks_SmartLockId",
                        column: x => x.SmartLockId,
                        principalTable: "SmartLocks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PinCode",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    KeyboardPwdId = table.Column<int>(type: "integer", nullable: false),
                    Pin = table.Column<string>(type: "text", nullable: false),
                    SmartLockId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PinCode", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PinCode_SmartLocks_SmartLockId",
                        column: x => x.SmartLockId,
                        principalTable: "SmartLocks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_AccessLogs_SmartLockId",
                table: "AccessLogs",
                column: "SmartLockId");

            migrationBuilder.CreateIndex(
                name: "IX_Card_SmartLockId",
                table: "Card",
                column: "SmartLockId");

            migrationBuilder.CreateIndex(
                name: "IX_EKey_SmartLockId",
                table: "EKey",
                column: "SmartLockId");

            migrationBuilder.CreateIndex(
                name: "IX_Fingerprint_SmartLockId",
                table: "Fingerprint",
                column: "SmartLockId");

            migrationBuilder.CreateIndex(
                name: "IX_PinCode_SmartLockId",
                table: "PinCode",
                column: "SmartLockId");

            migrationBuilder.CreateIndex(
                name: "IX_SmartLocks_UserId",
                table: "SmartLocks",
                column: "UserId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "AccessLogs");

            migrationBuilder.DropTable(
                name: "Card");

            migrationBuilder.DropTable(
                name: "EKey");

            migrationBuilder.DropTable(
                name: "Fingerprint");

            migrationBuilder.DropTable(
                name: "PinCode");

            migrationBuilder.DropTable(
                name: "SmartLocks");
        }
    }
}
