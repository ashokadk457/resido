using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace Resido.Database
{
    public class ResidoDbContextFactory : IDesignTimeDbContextFactory<ResidoDbContext>
    {
        public ResidoDbContext CreateDbContext(string[] args)
        {
            var config = new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.json") // or "appsettings.Development.json"
                .Build();

            var optionsBuilder = new DbContextOptionsBuilder<ResidoDbContext>();
            var connectionString = config.GetConnectionString("DefaultConnection");

            optionsBuilder.UseNpgsql(connectionString); // or UseSqlServer, UseMySql, etc.

            return new ResidoDbContext(optionsBuilder.Options);
        }
    }
}
