using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Resido.Migrations
{
    /// <inheritdoc />
    public partial class userdbchanges : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "IsEkeysSingnUp",
                table: "Users",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "UserStatus",
                table: "Users",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<int>(
                name: "UserUserTypeStatus",
                table: "Users",
                type: "integer",
                nullable: false,
                defaultValue: 0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "IsEkeysSingnUp",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "UserStatus",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "UserUserTypeStatus",
                table: "Users");
        }
    }
}
