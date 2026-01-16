namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for upload gateway detail.
    /// </summary>
    public class UploadGatewayDetailResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
