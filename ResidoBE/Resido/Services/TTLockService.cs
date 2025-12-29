using Resido.Database;
using Resido.Helper;
using Resido.Model;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO;
using Resido.Model.TTLockDTO.ResponseDTO;

namespace Resido.Services
{
    public class TTLockService
    {
        private const string BaseUrl = "https://euapi.ttlock.com/";
        private readonly string _clientId;
        private readonly string _clientSecret;
        private readonly ResidoDbContext _context;

        public TTLockService(ResidoDbContext context)
        {
            _context = context;
            // Live account
            _clientId = "5eb489f4b1f645d8ab7c95f7fe3e043c";
            _clientSecret = "91e0f8fbec6a8be1ba14cb6c793635a2";
        }

        private async Task<ResponseDTO<TResponse>?> PostToTTLockAsync<TRequest, TResponse>(
            string url,
            TRequest request)
            where TResponse : class
        {
            var responseDTO = new ResponseDTO<TResponse> { StatusCode = ResponseCode.Error };

            // Add timestamp if property exists
            var timestamp = GetTimestamp();
            var dateProp = typeof(TRequest).GetProperty("Date");
            if (dateProp != null)
            {
                dateProp.SetValue(request, timestamp);
            }

            var response = await TTLockHttpHelper.PostObjectWithResponseAsync(url, request);
            var responseBody = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                responseDTO.Data = JsonHelper.Deserialize<TResponse>(responseBody);

                if (responseDTO.Data is ITTLockErrorResponse errorResponse &&
                    errorResponse.Errcode == (int)ResponseCode.Success)
                {
                    responseDTO.SetSuccess();
                }
                else if (responseDTO.Data is ITTLockErrorResponse errorMessageProvider)
                {
                    responseDTO.SetMessage(errorMessageProvider.Errmsg);
                }
            }
            else
            {
                responseDTO.SetFailed(responseBody);
            }

            return responseDTO;
        }

        public async Task<ResponseDTO<RegisterResponseDTO>?> RegisterUserAsync(string username, string password)
        {
            var request = new TTLockRegisterUserRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = password
            };

            return await PostToTTLockAsync<TTLockRegisterUserRequestDTO, RegisterResponseDTO>(
                $"{BaseUrl}/v3/user/register", request);
        }

        public async Task<ResponseDTO<AccessTokenResponseDTO>?> GetAccessTokenAsync(string username, string password)
        {
            var request = new TTLockAccessTokenRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = password
            };

            return await PostToTTLockAsync<TTLockAccessTokenRequestDTO, AccessTokenResponseDTO>(
                $"{BaseUrl}/oauth2/token", request);
        }

        public async Task<ResponseDTO<TTLockApiResponseDTO>?> ResetPasswordAsync(string username, string newPassword)
        {
            var request = new TTLockResetPasswordRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = newPassword
            };

            var response = await TTLockHttpHelper.PostObjectAsync($"{BaseUrl}/v3/user/resetPassword", request);
            return await PostToTTLockAsync<TTLockResetPasswordRequestDTO, TTLockApiResponseDTO>(
               $"{BaseUrl}/oauth2/token", request);
        }

        private string GetTimestamp()
        {
            return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString();
        }
    }

}
