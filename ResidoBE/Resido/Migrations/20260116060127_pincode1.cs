using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Resido.Migrations
{
    /// <inheritdoc />
    public partial class pincode1 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Card_SmartLocks_SmartLockId",
                table: "Card");

            migrationBuilder.DropForeignKey(
                name: "FK_EKey_SmartLocks_SmartLockId",
                table: "EKey");

            migrationBuilder.DropForeignKey(
                name: "FK_Fingerprint_SmartLocks_SmartLockId",
                table: "Fingerprint");

            migrationBuilder.DropForeignKey(
                name: "FK_PinCode_SmartLocks_SmartLockId",
                table: "PinCode");

            migrationBuilder.DropPrimaryKey(
                name: "PK_PinCode",
                table: "PinCode");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Fingerprint",
                table: "Fingerprint");

            migrationBuilder.DropPrimaryKey(
                name: "PK_EKey",
                table: "EKey");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Card",
                table: "Card");

            migrationBuilder.DropColumn(
                name: "RecordTypeFromLock",
                table: "AccessLogs");

            migrationBuilder.RenameTable(
                name: "PinCode",
                newName: "PinCodes");

            migrationBuilder.RenameTable(
                name: "Fingerprint",
                newName: "Fingerprints");

            migrationBuilder.RenameTable(
                name: "EKey",
                newName: "EKeys");

            migrationBuilder.RenameTable(
                name: "Card",
                newName: "Cards");

            migrationBuilder.RenameIndex(
                name: "IX_PinCode_SmartLockId",
                table: "PinCodes",
                newName: "IX_PinCodes_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_Fingerprint_SmartLockId",
                table: "Fingerprints",
                newName: "IX_Fingerprints_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_EKey_SmartLockId",
                table: "EKeys",
                newName: "IX_EKeys_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_Card_SmartLockId",
                table: "Cards",
                newName: "IX_Cards_SmartLockId");

            migrationBuilder.AddColumn<string>(
                name: "Category",
                table: "SmartLocks",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Location",
                table: "SmartLocks",
                type: "text",
                nullable: true);

            migrationBuilder.AddPrimaryKey(
                name: "PK_PinCodes",
                table: "PinCodes",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Fingerprints",
                table: "Fingerprints",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_EKeys",
                table: "EKeys",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Cards",
                table: "Cards",
                column: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Cards_SmartLocks_SmartLockId",
                table: "Cards",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_EKeys_SmartLocks_SmartLockId",
                table: "EKeys",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_Fingerprints_SmartLocks_SmartLockId",
                table: "Fingerprints",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_PinCodes_SmartLocks_SmartLockId",
                table: "PinCodes",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Cards_SmartLocks_SmartLockId",
                table: "Cards");

            migrationBuilder.DropForeignKey(
                name: "FK_EKeys_SmartLocks_SmartLockId",
                table: "EKeys");

            migrationBuilder.DropForeignKey(
                name: "FK_Fingerprints_SmartLocks_SmartLockId",
                table: "Fingerprints");

            migrationBuilder.DropForeignKey(
                name: "FK_PinCodes_SmartLocks_SmartLockId",
                table: "PinCodes");

            migrationBuilder.DropPrimaryKey(
                name: "PK_PinCodes",
                table: "PinCodes");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Fingerprints",
                table: "Fingerprints");

            migrationBuilder.DropPrimaryKey(
                name: "PK_EKeys",
                table: "EKeys");

            migrationBuilder.DropPrimaryKey(
                name: "PK_Cards",
                table: "Cards");

            migrationBuilder.DropColumn(
                name: "Category",
                table: "SmartLocks");

            migrationBuilder.DropColumn(
                name: "Location",
                table: "SmartLocks");

            migrationBuilder.RenameTable(
                name: "PinCodes",
                newName: "PinCode");

            migrationBuilder.RenameTable(
                name: "Fingerprints",
                newName: "Fingerprint");

            migrationBuilder.RenameTable(
                name: "EKeys",
                newName: "EKey");

            migrationBuilder.RenameTable(
                name: "Cards",
                newName: "Card");

            migrationBuilder.RenameIndex(
                name: "IX_PinCodes_SmartLockId",
                table: "PinCode",
                newName: "IX_PinCode_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_Fingerprints_SmartLockId",
                table: "Fingerprint",
                newName: "IX_Fingerprint_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_EKeys_SmartLockId",
                table: "EKey",
                newName: "IX_EKey_SmartLockId");

            migrationBuilder.RenameIndex(
                name: "IX_Cards_SmartLockId",
                table: "Card",
                newName: "IX_Card_SmartLockId");

            migrationBuilder.AddColumn<int>(
                name: "RecordTypeFromLock",
                table: "AccessLogs",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddPrimaryKey(
                name: "PK_PinCode",
                table: "PinCode",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Fingerprint",
                table: "Fingerprint",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_EKey",
                table: "EKey",
                column: "Id");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Card",
                table: "Card",
                column: "Id");

            migrationBuilder.AddForeignKey(
                name: "FK_Card_SmartLocks_SmartLockId",
                table: "Card",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_EKey_SmartLocks_SmartLockId",
                table: "EKey",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_Fingerprint_SmartLocks_SmartLockId",
                table: "Fingerprint",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_PinCode_SmartLocks_SmartLockId",
                table: "PinCode",
                column: "SmartLockId",
                principalTable: "SmartLocks",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
