using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Resido.Database;
using Resido.Database.DBTable;

namespace Resido.Controllers
{
    public abstract class BaseApiController : ControllerBase
    {
        private readonly ResidoDbContext _context;

        protected BaseApiController(ResidoDbContext context)
        {
            _context = context;
        }

        /// <summary>
        /// Gets the Bearer token string from Authorization header.
        /// </summary>
        protected string BearerToken
        {
            get
            {
                var authHeader = HttpContext.Request.Headers["Authorization"].FirstOrDefault();
                if (!string.IsNullOrEmpty(authHeader) &&
                    authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
                {
                    return authHeader.Substring("Bearer ".Length).Trim();
                }
                return null;
            }
        }
        /// <summary>
        /// Gets the AccessRefreshToken entity from the database using the Bearer token.
        /// </summary>
        protected async Task<AccessRefreshToken?> GetAccessTokenEntityAsync()
        {
            var token = BearerToken;
            if (string.IsNullOrEmpty(token))
                return null;

            return await _context.AccessRefreshTokens
                .FirstOrDefaultAsync(t => t.AccessToken == token);
        }

        /// <summary>
        /// Gets the AccessRefreshToken entity from the database using the Bearer token.
        /// </summary>
        protected async Task<User?> GetCurrentUserAsync()
        {
            var token = BearerToken;
            if (string.IsNullOrEmpty(token))
                return null;

            var accessRefreshToken = await _context.AccessRefreshTokens
                  .Include(t => t.User.UserParameter)
                  .FirstOrDefaultAsync(t => t.AccessToken == token);

            return accessRefreshToken.User;
        }
    }
}
