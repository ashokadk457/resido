using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.ResponseDTO
{
    public class TTLockApiResponseDTO
    {
        public int ErrCode { get; set; }
        public string ErrMsg { get; set; } = string.Empty;

        public bool IsSuccess()
        {
            return ErrCode == 0;
        }
    }
}
