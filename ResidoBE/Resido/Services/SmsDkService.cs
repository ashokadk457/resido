using Newtonsoft.Json;
using Resido.Model.CommonDTO;
using System.Text;

namespace Resido.Services
{
    public class SmsDkService
    {

        private readonly HttpClient _httpClient;
        private readonly string _apiKey;

        public SmsDkService(IConfiguration configuration)
        {
            // read directly from appsettings.json
            _apiKey = configuration["SmsDkSettings:ApiKey"];
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {_apiKey}");
        }

        public async Task<ResponseDTO<string>> SendSmsAsync(SmsRequestDto smsRequest)
        {
            var responseDTO = new ResponseDTO<string>();
            try
            {

                smsRequest.SenderName = "ZafeConnect";

                string json = JsonConvert.SerializeObject(
                    smsRequest,
                    Formatting.None,
                    new JsonSerializerSettings { NullValueHandling = NullValueHandling.Ignore }
                );

                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync("https://api.sms.dk/v1/sms/send", content);

                if (!response.IsSuccessStatusCode)
                {
                    responseDTO.Message = await response.Content.ReadAsStringAsync();
                }
                else
                {
                    responseDTO.Message = await response.Content.ReadAsStringAsync();
                    responseDTO.SetSuccess();
                }
            }
            catch (Exception ex)
            {
                responseDTO.SetMessage(ex.Message);
            }
            return responseDTO;

        }
        public class SmsRequestDto
        {
            [JsonProperty("receiver")]
            public string Receiver { get; set; }

            [JsonProperty("senderName")]
            public string SenderName { get; set; }

            [JsonProperty("message")]
            public string Message { get; set; }

            [JsonProperty("format")]
            public string Format { get; set; } = "gsm";

            [JsonProperty("encoding")]
            public string Encoding { get; set; } = "utf8";
        }
    }
}
