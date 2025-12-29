using Resido.Helper;
using Resido.Model.TTLockDTO.ResponseDTO;
using System.ComponentModel.DataAnnotations;

namespace Resido.Database.DBTable
{
    public class AccessRefreshToken
    {
        [Key]
        public Guid Id { get; set; }
        public virtual User User { get; set; }
        public Guid UserId { get; set; }
        public string AccessToken { get; set; }
        public long Uid { get; set; }
        public long ExpiresIn { get; set; }
        public string Scope { get; set; }
        public string RefreshToken { get; set; }
        /// <summary>
        /// UTC date when token was issued/stored.
        /// </summary>
        public DateTime IssuedAtUtc { get; set; }

        public AccessRefreshToken()
        {

        }

        public AccessRefreshToken(AccessTokenResponseDTO? accessToken)
        {
            AccessToken = accessToken.AccessToken;
            Uid = accessToken.Uid;
            ExpiresIn = accessToken.ExpiresIn;
            Scope = accessToken.Scope;
            RefreshToken = accessToken.RefreshToken;
            IssuedAtUtc = DateTimeHelper.GetUtcTime();
        }
        /// <summary>
        /// Checks whether the access token is still valid based on its lifetime.
        /// </summary>
        public bool IsValidAccessToken()
        {
            if (string.IsNullOrWhiteSpace(AccessToken))
                return false;

            //{08-03-0001 16:17:59}
            var expiryTime = DateTimeHelper.GetUtcTime().AddSeconds(ExpiresIn);
            return DateTimeHelper.GetUtcTime() < expiryTime;
        }
    }
}
