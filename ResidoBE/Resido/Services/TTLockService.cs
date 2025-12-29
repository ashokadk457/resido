using Resido.Database;
using Resido.Helper;
using Resido.Model;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.RequestDTO;
using Resido.Model.TTLockDTO.RequestDTO.CardRq;
using Resido.Model.TTLockDTO.RequestDTO.EkeysRq;
using Resido.Model.TTLockDTO.RequestDTO.LockRq;
using Resido.Model.TTLockDTO.RequestDTO.PasscodeRq;
using Resido.Model.TTLockDTO.ResponseDTO;
using Resido.Model.TTLockDTO.ResponseDTO.CardRsp;
using Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp;
using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;
using Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp;

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
        /// <summary>
        /// Builds a query string from an object's public properties.
        /// Null values are skipped. Values are URL-encoded.
        /// </summary>
        public static string BuildQueryString(object obj)
        {
            if (obj == null) return string.Empty;

            var props = obj.GetType().GetProperties();
            var queryParams = new List<string>();

            foreach (var prop in props)
            {
                var value = prop.GetValue(obj, null);
                if (value != null)
                {
                    var encodedName = Uri.EscapeDataString(prop.Name);
                    var encodedValue = Uri.EscapeDataString(value.ToString()!);
                    queryParams.Add($"{encodedName}={encodedValue}");
                }
            }

            return string.Join("&", queryParams);
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
        private async Task<ResponseDTO<TResponse>?> GetFromTTLockAsync<TRequest, TResponse>(
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

            // Build query string from request object
            var queryParams = BuildQueryString(request);
            var fullUrl = $"{url}?{queryParams}";

            var response = await TTLockHttpHelper.GetObjectWithResponseAsync(fullUrl);
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
            var request = new RegisterUserRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = password
            };

            return await PostToTTLockAsync<RegisterUserRequestDTO, RegisterResponseDTO>(
                $"{BaseUrl}/v3/user/register", request);
        }

        public async Task<ResponseDTO<AccessTokenResponseDTO>?> GetAccessTokenAsync(string username, string password)
        {
            var request = new AccessTokenRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = password
            };

            return await PostToTTLockAsync<AccessTokenRequestDTO, AccessTokenResponseDTO>(
                $"{BaseUrl}/oauth2/token", request);
        }

        public async Task<ResponseDTO<ApiResponseDTO>?> ResetPasswordAsync(string username, string newPassword)
        {
            var request = new ResetPasswordRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = _clientSecret,
                Username = username,
                Password = newPassword
            };

            var response = await TTLockHttpHelper.PostObjectAsync($"{BaseUrl}/v3/user/resetPassword", request);
            return await PostToTTLockAsync<ResetPasswordRequestDTO, ApiResponseDTO>(
               $"{BaseUrl}/oauth2/token", request);
        }

        public async Task<ResponseDTO<ListKeysResponseDTO>?> ListKeysAsync(ListKeysRequestDTO ttLockList)
        {
            var request = new ListKeysRequestDTO
            {
                ClientId = _clientId,
                ClientSecret = ttLockList.AccessToken,
                LockAlias = ttLockList.LockAlias,
                GroupId = ttLockList.GroupId,
                PageNo = ttLockList.PageNo,
                PageSize = ttLockList.PageSize,
                Date = GetTimestamp()
            };

            return await PostToTTLockAsync<ListKeysRequestDTO, ListKeysResponseDTO>(
                $"{BaseUrl}/v3/key/list", request);
        }
        public async Task<ResponseDTO<DeleteKeyResponseDTO>?> DeleteKeyAsync(string accessToken, int keyId)
        {
            var request = new DeleteKeyRequestDTO
            {
                ClientId = _clientId,
                AccessToken = accessToken,
                KeyId = keyId,
                Date = GetTimestamp()
            };

            return await PostToTTLockAsync<DeleteKeyRequestDTO, DeleteKeyResponseDTO>(
                $"{BaseUrl}/v3/key/delete", request);
        }
        public async Task<ResponseDTO<UnfreezeKeyResponseDTO>?> UnfreezeKeyAsync(string accessToken, int keyId)
        {
            var request = new UnfreezeKeyRequestDTO
            {
                ClientId = _clientId,
                AccessToken = accessToken,
                KeyId = keyId,
                Date = GetTimestamp()
            };

            return await PostToTTLockAsync<UnfreezeKeyRequestDTO, UnfreezeKeyResponseDTO>(
                $"{BaseUrl}/v3/key/unfreeze", request);
        }

        public async Task<ResponseDTO<UpdateKeyResponseDTO>?> UpdateKeyAsync(string accessToken, UpdateKeyRequestDTO dto)
        {
            var request = new TTLockUpdateKeyRequestDTO
            {
                ClientId = _clientId,
                Date = GetTimestamp(),
                AccessToken = accessToken,
                KeyId = dto.KeyId,
                KeyName = dto.KeyName,
                RemoteEnable = dto.RemoteEnable
            };

            return await PostToTTLockAsync<TTLockUpdateKeyRequestDTO, UpdateKeyResponseDTO>(
                $"{BaseUrl}/v3/key/update", request);
        }

        public async Task<ResponseDTO<ChangeKeyPeriodResponseDTO>?> ChangeKeyPeriodAsync(string accessToken, ChangeKeyPeriodRequestDTO dto)
        {
            var request = new TTLockChangeKeyPeriodRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                KeyId = dto.KeyId,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate
            };

            return await PostToTTLockAsync<TTLockChangeKeyPeriodRequestDTO, ChangeKeyPeriodResponseDTO>(
                $"{BaseUrl}/v3/key/changePeriod", request);
        }

        public async Task<ResponseDTO<KeyAuthorizeResponseDTO>?> AuthorizeKeyAsync(
            string accessToken,
            int lockId,
            int keyId)
        {
            var request = new TTLockKeyAuthorizeRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = lockId,
                KeyId = keyId
            };

            return await PostToTTLockAsync<TTLockKeyAuthorizeRequestDTO, KeyAuthorizeResponseDTO>(
                $"{BaseUrl}/v3/key/authorize", request);
        }
        public async Task<ResponseDTO<KeyUnauthorizeResponseDTO>?> UnauthorizeKeyAsync(
    string accessToken,
    int lockId,
    int keyId)
        {
            var request = new TTLockKeyUnauthorizeRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = lockId,
                KeyId = keyId
            };

            return await PostToTTLockAsync<TTLockKeyUnauthorizeRequestDTO, KeyUnauthorizeResponseDTO>(
                $"{BaseUrl}/v3/key/unauthorize", request);
        }
        public async Task<ResponseDTO<SendKeyResponseDTO>?> SendKeyAsync(string accessToken, SendKeyRequestDTO dto)
        {
            var request = new TTLockSendKeyRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                ReceiverUsername = dto.ReceiverUsername,
                KeyName = dto.KeyName,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate,
                Remarks = dto.Remarks,
                RemoteEnable = dto.RemoteEnable,
                KeyRight = dto.KeyRight,
                CreateUser = dto.CreateUser
            };

            return await PostToTTLockAsync<TTLockSendKeyRequestDTO, SendKeyResponseDTO>(
                $"{BaseUrl}/v3/key/send", request);
        }
        public async Task<ResponseDTO<GetKeyboardPwdResponseDTO>?> GetKeyboardPwdAsync(string accessToken, GetKeyboardPwdRequestDTO dto)
        {
            var request = new TTLockGetKeyboardPwdRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                KeyboardPwdType = (int)dto.KeyboardPwdType,
                KeyboardPwdName = dto.KeyboardPwdName,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate
            };

            return await PostToTTLockAsync<TTLockGetKeyboardPwdRequestDTO, GetKeyboardPwdResponseDTO>(
                $"{BaseUrl}/v3/keyboardPwd/get", request);
        }
        public async Task<ResponseDTO<AddKeyboardPwdResponseDTO>?> AddKeyboardPwdAsync(string accessToken, AddKeyboardPwdRequestDTO dto)
        {
            var request = new TTLockAddKeyboardPwdRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                KeyboardPwd = dto.KeyboardPwd,
                KeyboardPwdName = dto.KeyboardPwdName,
                KeyboardPwdType = dto.KeyboardPwdType,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate,
                AddType = (int)dto.AddType
            };

            return await PostToTTLockAsync<TTLockAddKeyboardPwdRequestDTO, AddKeyboardPwdResponseDTO>(
                $"{BaseUrl}/v3/keyboardPwd/add", request);
        }
        public async Task<ResponseDTO<ListKeyboardPwdResponseDTO>?> ListKeyboardPwdAsync(string accessToken, ListKeyboardPwdRequestDTO dto)
        {
            var request = new TTLockListKeyboardPwdRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                SearchStr = dto.SearchStr,
                PageNo = dto.PageNo,
                PageSize = dto.PageSize,
                OrderBy = dto.OrderBy
            };

            return await GetFromTTLockAsync<TTLockListKeyboardPwdRequestDTO, ListKeyboardPwdResponseDTO>(
                $"{BaseUrl}/v3/lock/listKeyboardPwd", request);
        }
        public async Task<ResponseDTO<DeleteKeyboardPwdResponseDTO>?> DeleteKeyboardPwdAsync(string accessToken, DeleteKeyboardPwdRequestDTO dto)
        {
            var request = new TTLockDeleteKeyboardPwdRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                KeyboardPwdId = dto.KeyboardPwdId,
                DeleteType = (int)dto.DeleteType
            };

            return await PostToTTLockAsync<TTLockDeleteKeyboardPwdRequestDTO, DeleteKeyboardPwdResponseDTO>(
                $"{BaseUrl}/v3/keyboardPwd/delete", request);
        }
        public async Task<ResponseDTO<ChangeKeyboardPwdResponseDTO>?> ChangeKeyboardPwdAsync(string accessToken, ChangeKeyboardPwdRequestDTO dto)
        {
            var request = new TTLockChangeKeyboardPwdRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                KeyboardPwdId = dto.KeyboardPwdId,
                KeyboardPwdName = dto.KeyboardPwdName,
                NewKeyboardPwd = dto.NewKeyboardPwd,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate,
                ChangeType = dto.ChangeType.HasValue ? (int)dto.ChangeType.Value : null
            };

            return await PostToTTLockAsync<TTLockChangeKeyboardPwdRequestDTO, ChangeKeyboardPwdResponseDTO>(
                $"{BaseUrl}/v3/keyboardPwd/change", request);
        }

        public async Task<ResponseDTO<AddCardResponseDTO>?> AddCardAsync(string accessToken, AddCardRequestDTO dto, bool useReversedApi = true)
        {
            var request = new TTLockAddCardRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                CardNumber = dto.CardNumber,
                CardName = dto.CardName,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate,
                CardType = dto.CardType,
                CyclicConfig = dto.CyclicConfig,
                AddType = (int)dto.AddType
            };

            // Choose endpoint based on whether reversed card number API should be used
            var endpoint = useReversedApi
                ? $"{BaseUrl}/v3/identityCard/addForReversedCardNumber"
                : $"{BaseUrl}/v3/identityCard/add";

            return await PostToTTLockAsync<TTLockAddCardRequestDTO, AddCardResponseDTO>(endpoint, request);
        }

        public async Task<ResponseDTO<ListIdentityCardResponseDTO>?> ListIdentityCardsAsync(string accessToken, ListIdentityCardRequestDTO dto)
        {
            var request = new TTLockListIdentityCardRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                SearchStr = dto.SearchStr,
                PageNo = dto.PageNo,
                PageSize = dto.PageSize,
                OrderBy = dto.OrderBy
            };

            return await GetFromTTLockAsync<TTLockListIdentityCardRequestDTO, ListIdentityCardResponseDTO>(
                $"{BaseUrl}/v3/identityCard/list", request);
        }

        public async Task<ResponseDTO<DeleteCardResponseDTO>?> DeleteCardAsync(string accessToken, DeleteCardRequestDTO dto)
        {
            var request = new TTLockDeleteCardRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                CardId = dto.CardId,
                DeleteType = (int)dto.DeleteType
            };

            return await PostToTTLockAsync<TTLockDeleteCardRequestDTO, DeleteCardResponseDTO>(
                $"{BaseUrl}/v3/identityCard/delete", request);
        }

        public async Task<ResponseDTO<ChangeCardPeriodResponseDTO>?> ChangeCardPeriodAsync(string accessToken, ChangeCardPeriodRequestDTO dto)
        {
            var request = new TTLockChangeCardPeriodRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                CardId = dto.CardId,
                StartDate = dto.StartDate,
                EndDate = dto.EndDate,
                CyclicConfig = dto.CyclicConfig,
                ChangeType = (int)dto.ChangeType
            };

            return await PostToTTLockAsync<TTLockChangeCardPeriodRequestDTO, ChangeCardPeriodResponseDTO>(
                $"{BaseUrl}/v3/identityCard/changePeriod", request);
        }

        public async Task<ResponseDTO<ClearCardResponseDTO>?> ClearCardAsync(string accessToken, ClearCardRequestDTO dto)
        {
            var request = new TTLockClearCardRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId
            };

            return await PostToTTLockAsync<TTLockClearCardRequestDTO, ClearCardResponseDTO>(
                $"{BaseUrl}/v3/identityCard/clear", request);
        }
        public async Task<ResponseDTO<RenameCardResponseDTO>?> RenameCardAsync(string accessToken, RenameCardRequestDTO dto)
        {
            var request = new TTLockRenameCardRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                CardId = dto.CardId,
                CardName = dto.CardName
            };

            return await PostToTTLockAsync<TTLockRenameCardRequestDTO, RenameCardResponseDTO>(
                $"{BaseUrl}/v3/identityCard/rename", request);
        }


        public async Task<ResponseDTO<DeleteLockResponseDTO>?> DeleteLockAsync(string accessToken, DeleteLockRequestDTO dto)
        {
            var request = new TTLockDeleteLockRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId
            };

            return await PostToTTLockAsync<TTLockDeleteLockRequestDTO, DeleteLockResponseDTO>(
                $"{BaseUrl}/v3/lock/delete", request);
        }
        public async Task<ResponseDTO<RenameLockResponseDTO>?> RenameLockAsync(string accessToken, RenameLockRequestDTO dto)
        {
            var request = new TTLockRenameLockRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockId = dto.LockId,
                LockAlias = dto.LockAlias
            };

            return await PostToTTLockAsync<TTLockRenameLockRequestDTO, RenameLockResponseDTO>(
                $"{BaseUrl}/v3/lock/rename", request);
        }

        public async Task<ResponseDTO<InitializeLockResponseDTO>?> InitializeLockAsync(string accessToken, InitializeLockRequestDTO dto)
        {
            var request = new TTLockInitializeLockRequestDTO
            {
                ClientId = _clientId,
                Date = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(),
                AccessToken = accessToken,
                LockAlias = dto.LockAlias,
                LockData = dto.LockData,
                GroupId = dto.GroupId,
                NbInitSuccess = dto.NbInitSuccess
            };

            return await PostToTTLockAsync<TTLockInitializeLockRequestDTO, InitializeLockResponseDTO>(
                $"{BaseUrl}/v3/lock/initialize", request);
        }

        private string GetTimestamp()
        {
            return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString();
        }
    }

}
