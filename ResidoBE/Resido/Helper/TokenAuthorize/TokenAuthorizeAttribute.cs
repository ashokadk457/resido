using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.EntityFrameworkCore;
using Resido.Database;

namespace Resido.Helper.TokenAuthorize
{
    public class TokenAuthorizeAttribute : Attribute, IAsyncAuthorizationFilter
    {
        public async Task OnAuthorizationAsync(AuthorizationFilterContext context)
        {
            var dbContext = context.HttpContext.RequestServices.GetService(typeof(ResidoDbContext)) as ResidoDbContext;

            if (dbContext == null)
            {
                context.Result = new StatusCodeResult(StatusCodes.Status500InternalServerError);
                return;
            }

            var authHeader = context.HttpContext.Request.Headers["Authorization"].FirstOrDefault();
            if (string.IsNullOrEmpty(authHeader) || !authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
            {
                context.Result = new UnauthorizedObjectResult(new
                {
                    key = "MissingBearerToken",
                    message = "Authorization token is missing."
                });
                return;
            }

            var tokenValue = authHeader.Substring("Bearer ".Length).Trim();

            var tokenEntity = await dbContext.AccessRefreshTokens
                .Include(t => t.User)
                .FirstOrDefaultAsync(t => t.AccessToken == tokenValue);

            if (tokenEntity == null || !tokenEntity.IsValidAccessToken())
            {
                context.Result = new UnauthorizedObjectResult(new
                {
                    key = "InvalidAccessToken",
                    message = "Invalid access token or token has expired."
                });
                return;
            }

            // If token is valid, store it in HttpContext for later use
            context.HttpContext.Items["AccessTokenEntity"] = tokenEntity;
        }
    }
}
