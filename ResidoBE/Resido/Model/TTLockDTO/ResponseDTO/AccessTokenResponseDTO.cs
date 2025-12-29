using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.ResponseDTO
{
    public class AccessTokenResponseDTO: AuthDataDTO
    {

        [JsonPropertyName("uid")]
        public long Uid { get; set; }
        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; }

        [JsonPropertyName("expires_in")]
        public long ExpiresIn { get; set; }

        [JsonPropertyName("scope")]
        public string Scope { get; set; }

        [JsonPropertyName("refresh_token")]
        public string RefreshToken { get; set; }

    }
    public class AuthDataDTO
    {
        public string? FullName { get; set; }
    }

}
