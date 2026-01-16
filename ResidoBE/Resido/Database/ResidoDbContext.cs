using Microsoft.EntityFrameworkCore;
using Resido.Database.DBTable;

namespace Resido.Database
{
    public class ResidoDbContext : DbContext
    {
        public ResidoDbContext(DbContextOptions<ResidoDbContext> options) : base(options)
        {

        }
        public DbSet<User> Users { get; set; } = null!;
        public DbSet<AccessRefreshToken> AccessRefreshTokens { get; set; } = null!;
        public DbSet<Country> Countries { get; set; } = null!;
        public DbSet<SmartLock> SmartLocks { get; set; } = null!;
        public DbSet<AccessLog> AccessLogs { get; set; } = null!;
    }
}
