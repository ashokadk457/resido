using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Resido.Migrations
{
    /// <inheritdoc />
    public partial class userdbchanges1 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.RenameColumn(
                name: "UserUserTypeStatus",
                table: "Users",
                newName: "UserType");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.RenameColumn(
                name: "UserType",
                table: "Users",
                newName: "UserUserTypeStatus");
        }
    }
}
