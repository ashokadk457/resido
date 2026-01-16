namespace Resido.Model.DTO
{
    public class AccessLogDayGroupDTO
    {
        public DateTime Date { get; set; } // UTC Date (yyyy-MM-dd)
        public List<AccessLogResponseDTO> Logs { get; set; } = new();
    }
    public class AccessLogResponseDTO
    {
        public Guid Id { get; set; }
        public int LockId { get; set; }
        public string? LockMac { get; set; }
        public int RecordType { get; set; }
        public string? RecordTypeDescription { get; set; }
        public string? Username { get; set; }
        public string? KeyboardPwd { get; set; }
        public int BatteryPercentage { get; set; }
        public bool IsAccessSuccessful { get; set; }
        public DateTime LockEventUtcTime { get; set; }
        public DateTime ServerReceivedUtcTime { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
