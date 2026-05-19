using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Resido.Migrations
{
    /// <inheritdoc />
    public partial class changeInAccessLog : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_AccessLogs_SmartLocks_SmartLockId",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "IsAccessSuccessful",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "LockEventLocalTime",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "ServerReceivedLocalTime",
                table: "AccessLogs");

            migrationBuilder.RenameColumn(
                name: "ServerReceivedUtcTime",
                table: "AccessLogs",
                newName: "ServerDate");

            migrationBuilder.RenameColumn(
                name: "LockEventUtcTime",
                table: "AccessLogs",
                newName: "LockDate");

            migrationBuilder.RenameColumn(
                name: "BatteryPercentage",
                table: "AccessLogs",
                newName: "RecordTypeFromLock");

            migrationBuilder.AlterColumn<Guid>(
                name: "SmartLockId",
                table: "AccessLogs",
                type: "uuid",
                nullable: true,
                oldClrType: typeof(Guid),
                oldType: "uuid");

            migrationBuilder.AddColumn<int>(
                name: "ElectricQuantity",
                table: "AccessLogs",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<string>(
                name: "NewPassword",
                table: "AccessLogs",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Password",
                table: "AccessLogs",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<long>(
                name: "RecordId",
                table: "AccessLogs",
                type: "bigint",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "Uid",
                table: "AccessLogs",
                type: "integer",
                nullable: true);

            migrationBuilder.AddForeignKey(
                name: "FK_AccessLogs_SmartLocks_SmartLockId",
                table: "AccessLogs",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_AccessLogs_SmartLocks_SmartLockId",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "ElectricQuantity",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "NewPassword",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "Password",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "RecordId",
                table: "AccessLogs");

            migrationBuilder.DropColumn(
                name: "Uid",
                table: "AccessLogs");

            migrationBuilder.RenameColumn(
                name: "ServerDate",
                table: "AccessLogs",
                newName: "ServerReceivedUtcTime");

            migrationBuilder.RenameColumn(
                name: "RecordTypeFromLock",
                table: "AccessLogs",
                newName: "BatteryPercentage");

            migrationBuilder.RenameColumn(
                name: "LockDate",
                table: "AccessLogs",
                newName: "LockEventUtcTime");

            migrationBuilder.AlterColumn<Guid>(
                name: "SmartLockId",
                table: "AccessLogs",
                type: "uuid",
                nullable: false,
                defaultValue: new Guid("00000000-0000-0000-0000-000000000000"),
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "IsAccessSuccessful",
                table: "AccessLogs",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<long>(
                name: "LockEventLocalTime",
                table: "AccessLogs",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.AddColumn<long>(
                name: "ServerReceivedLocalTime",
                table: "AccessLogs",
                type: "bigint",
                nullable: false,
                defaultValue: 0L);

            migrationBuilder.AddForeignKey(
                name: "FK_AccessLogs_SmartLocks_SmartLockId",
                table: "AccessLogs",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
