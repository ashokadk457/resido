using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.ResponseDTO
{
    public class TTLockResponseCodeDTO: ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; }
    }
}
