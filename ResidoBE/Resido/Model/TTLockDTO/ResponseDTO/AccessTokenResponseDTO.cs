using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.ResponseDTO
{
    using Newtonsoft.Json;

    public class AccessTokenResponseDTO : ResponseCodeDTO
    {
        [JsonProperty("uid")]
        public long Uid { get; set; }

        [JsonProperty("access_token")]
        public string AccessToken { get; set; }

        [JsonProperty("expires_in")]
        public long ExpiresIn { get; set; }

        [JsonProperty("scope")]
        public string Scope { get; set; }

        [JsonProperty("refresh_token")]
        public string RefreshToken { get; set; }

        [JsonProperty("openid")]
        public long OpenId { get; set; }

        [JsonProperty("token_type")]
        public string TokenType { get; set; }
        public string? FullName { get; set; }

    }
}
