using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Model.CommonDTO;
using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;
using Resido.Model.TTLockDTO.Webhook;
using Resido.Services.DAL;

namespace Resido.Controllers
{
    [Route("api/[controller]/[action]")]
    [ApiController]
    public class TTLockWebHookController : ControllerBase
    {
        private readonly ResidoDbContext _context;
        private readonly ILogger<TTLockWebHookController> _logger;
        private readonly CommonDBLogic _commonDBLogic;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        private static readonly Dictionary<int, string> appRecordTypeDescriptions = new()
{
    { 1, "Unlock by Bluetooth" },
    { 4, "Unlock by Passcode Success" },
    { 5, "Modify a Passcode on the Lock" },
    { 6, "Delete a Passcode on the Lock" },
    { 7, "Unlock by Passcode Failed - Unknown Passcode" },
    { 8, "Clear Passcodes from the Lock" },
    { 9, "Passcode Be Squeezed Out" },
    { 10, "Unlock with Passcode and Delete Previous Passcodes" },
    { 11, "Unlock by Passcode Failed - Passcode Expired" },
    { 12, "Unlock by Passcode Failed - Run Out of Memory" },
    { 13, "Unlock by Passcode Failed - Passcode in Blacklist" },
    { 14, "Lock Power On" },
    { 15, "Add Card Success" },
    { 16, "Clear Cards" },
    { 17, "Unlock by Card Success" },
    { 18, "Delete a Card" },
    { 19, "Unlock by Wrist Strap Success" },
    { 20, "Unlock by Fingerprint Success" },
    { 21, "Add Fingerprint Success" },
    { 22, "Unlock by Fingerprint Failed - Fingerprint Expired" },
    { 23, "Delete Fingerprint" },
    { 24, "Clear Fingerprints" },
    { 25, "Unlock by Card Failed - Card Expired" },
    { 26, "Lock by Bluetooth" },
    { 27, "Unlock by Mechanical Key" },
    { 28, "Unlock by Gateway" },
    { 29, "Force Applied on Lock" },
    { 30, "Door Sensor Closed" },
    { 31, "Door Sensor Open" },
    { 32, "Open from Inside" },
    { 33, "Lock by Fingerprint" },
    { 34, "Lock by Passcode" },
    { 35, "Lock by Card" },
    { 36, "Lock by Mechanical Key" },
    { 37, "App Button Control (Rise/Fall/Stop/Lock)" },
    { 38, "Unlock by Passcode Failed - Door Double Locked" },
    { 39, "Unlock by IC Card Failed - Door Double Locked" },
    { 40, "Unlock by Fingerprint Failed - Door Double Locked" },
    { 41, "Unlock by App Failed - Door Double Locked" },
    { 42, "Received New Local Mail" },
    { 43, "Received New Mail from Other Cities" },
    { 44, "Tamper Alert" },
    { 45, "Auto Lock" },
    { 46, "Unlock by Unlock Key" },
    { 47, "Lock by Lock Key" },
    { 48, "System Locked Due to Multiple Invalid Attempts" },
    { 49, "Unlock by Hotel Card" },
    { 50, "Unlocked Due to High Temperature" },
    { 51, "Unlock by Card Failed - Card in Blacklist" },
    { 52, "Dead Lock with App" },
    { 53, "Dead Lock with Passcode" },
    { 54, "Car Left (Parking Lock)" },
    { 55, "Remote Control Lock or Unlock" },
    { 57, "Unlock with QR Code Success" },
    { 58, "Unlock with QR Code Failed - Expired" },
    { 59, "Double Locked" },
    { 60, "Cancel Double Lock" },
    { 61, "Lock with QR Code Success" },
    { 62, "Lock with QR Code Failed - Double Locked" },
    { 63, "Auto Unlock in Passage Mode" },
    { 64, "Door Unclosed Alarm" },
    { 65, "Failed to Unlock" },
    { 66, "Failed to Lock" },
    { 67, "Face Unlock Success" },
    { 68, "Face Unlock Failed - Door Locked from Inside" },
    { 69, "Lock with Face" },
    { 70, "Face Registration Success" },
    { 71, "Face Unlock Failed - Expired or Ineffective" },
    { 72, "Delete Face Success" },
    { 73, "Clear Face Success" },
    { 74, "IC Card Unlock Failed - CPU Secure Information Error" },
    { 75, "App Authorized Button Unlock Success" },
    { 76, "Gateway Authorized Button Unlock Success" },
    { 77, "Dual Authentication Bluetooth Verification Success - Waiting for Second User" },
    { 78, "Dual Authentication Passcode Verification Success - Waiting for Second User" },
    { 79, "Dual Authentication Fingerprint Verification Success - Waiting for Second User" },
    { 80, "Dual Authentication IC Card Verification Success - Waiting for Second User" },
    { 81, "Dual Authentication Face Verification Success - Waiting for Second User" },
    { 82, "Dual Authentication Wireless Key Verification Success - Waiting for Second User" },
    { 83, "Dual Authentication Palm Vein Verification Success - Waiting for Second User" },
    { 84, "Palm Vein Unlock Success" },
    { 85, "Palm Vein Unlock Success" },
    { 86, "Lock with Palm Vein" },
    { 87, "Register Palm Vein Success" },
    { 88, "Palm Vein Unlock Failed - Expired or Ineffective" },
    { 89, "Delete Palm Vein Success" },
    { 90, "Clear Palm Vein Success" },
    { 91, "Failed to Unlock with IC Card" },
    { 92, "Administrator Password Unlock" },
    { 93, "Add Password Success (Custom or Keyboard)" }
};

        private static readonly Dictionary<int, string> RecordTypeDescriptions = new()
        {
            {1, "Unlock by App"},
            {4, "Unlock by Passcode"},
            {5, "Rise the lock (parking lock)"},
            {6, "Lower the lock (parking lock)"},
            {7, "Unlock by IC card"},
            {8, "Unlock by Fingerprint"},
            {9, "Unlock by Wrist strap"},
            {10, "Unlock by Mechanical key"},
            {11, "Lock by App"},
            {12, "Unlock by gateway"},
            {29, "Apply some force on the Lock"},
            {30, "Door sensor closed"},
            {31, "Door sensor open"},
            {32, "Open from inside"},
            {33, "Lock by fingerprint"},
            {34, "Lock by passcode"},
            {35, "Lock by IC card"},
            {36, "Lock by Mechanical key"},
            {37, "Use APP button to control the lock"},
            {42, "Received new local mail"},
            {43, "Received new other cities' mail"},
            {44, "Tamper alert"},
            {45, "Auto Lock"},
            {46, "Unlock by unlock key"},
            {47, "Lock by lock key"},
            {48, "System locked"},
            {49, "Unlock by hotel card"},
            {50, "Unlocked due to high temperature"},
            {51, "Try to unlock with a deleted card"},
            {52, "Dead lock with APP"},
            {53, "Dead lock with passcode"},
            {54, "The car left (parking lock)"},
            {55, "Use remote control lock or unlock"},
            {57, "Unlock with QR code success"},
            {58, "Unlock with QR code failed"},
            {59, "Double locked"},
            {60, "Cancel double lock"},
            {61, "Lock with QR code success"},
            {62, "Lock with QR code failed, double locked"},
            {63, "Auto unlock at passage mode"},
            {64, "Door unclosed alarm"},
            {65, "Failed to unlock"},
            {66, "Failed to lock"},
            {67, "Face unlock success"},
            {68, "Face unlock failed - door locked from inside"},
            {69, "Lock with face"},
            {71, "Face unlock failed - expired or ineffective"},
            {75, "Unlocked by App granting"},
            {76, "Unlocked by remote granting"},
            {77, "Dual authentication Bluetooth unlock success"},
            {78, "Dual authentication password unlock success"},
            {79, "Dual authentication fingerprint unlock success"},
            {80, "Dual authentication IC card unlock success"},
            {81, "Dual authentication face card unlock success"},
            {82, "Dual authentication wireless key unlock success"},
            {83, "Dual authentication palm vein unlock success"},
            {84, "Palm vein unlock success"},
            {85, "Palm vein unlock success"},
            {86, "Lock with palm vein"},
            {88, "Palm vein unlock failed"},
            {92, "Administrator password to unlock"}
        };
        public TTLockWebHookController(
           ResidoDbContext context,
           ILogger<TTLockWebHookController> logger,
           CommonDBLogic commonDBLogic,
           IServiceScopeFactory serviceScopeFactory
       )
        {
            _context = context;
            _logger = logger;
            _commonDBLogic = commonDBLogic;
            _serviceScopeFactory = serviceScopeFactory;
        }

        [HttpPost]
        public async Task<IActionResult> Callback([FromForm] TTLockWebhookDto formData)
        {
            try
            {
                if (!(formData.Records?.Any() ?? false))
                {
                    _logger.LogCritical($"formData no records found : {JsonConvert.SerializeObject(formData)}");
                    return Ok();
                }

                _logger.LogCritical($"formData records found : {JsonConvert.SerializeObject(formData)}");

                var records = JsonConvert.DeserializeObject<List<TTLockRecordDto>>(formData.Records) ?? new();
                _logger.LogCritical($"records deserialize : {JsonConvert.SerializeObject(records)}");

                if (!records.Any())
                {
                    _logger.LogCritical("No records after deserialization.");
                    return Ok();
                }
                var smartLock = await _context.SmartLocks
                   .FirstOrDefaultAsync(a => a.TTLockId == formData.LockId);

                SaveHistoryAndNotifyBackground(records, formData, smartLock);

            }
            catch (Exception ex)
            {
                _logger.LogCritical($"Received Exception: {ex.Message}");
            }

            return Ok();
        }
        private void SaveHistoryAndNotifyBackground(
List<TTLockRecordDto> records,
TTLockWebhookDto formData,
SmartLock? smartLock)
        {
            if (smartLock != null)
            {
                // Run fire-and-forget in background
                _ = Task.Run(async () =>
                {
                    using (var scope = _serviceScopeFactory.CreateScope())
                    {
                        var logger = scope.ServiceProvider.GetRequiredService<ILogger<TTLockWebHookController>>();
                        var scopedDb = scope.ServiceProvider.GetRequiredService<ResidoDbContext>();
                        var commonDBLogic = scope.ServiceProvider.GetRequiredService<CommonDBLogic>();

                        foreach (var record in records)
                        {
                            try
                            {
                                var history = new AccessLog
                                {
                                    LockId = formData.LockId,
                                    LockMac = formData.LockMac,
                                    RecordType = record.RecordType,
                                    RecordTypeDescription =
                                    RecordTypeDescriptions.TryGetValue(record.RecordType, out var desc)
                                        ? desc : "Unknown",
                                    Username = record.Username,
                                    KeyboardPwd = record.KeyboardPwd,
                                    Success = record.Success,
                                    SmartLockId= smartLock.Id,
                                    BatteryPercentage = record.ElectricQuantity,
                                    LockEventLocalTime = record.LockDate,
                                    ServerReceivedLocalTime = record.ServerDate,
                                    LockEventUtcTime = DateTimeOffset.FromUnixTimeMilliseconds(record.LockDate).UtcDateTime,
                                    ServerReceivedUtcTime = DateTimeOffset.FromUnixTimeMilliseconds(record.ServerDate).UtcDateTime,
                                    CreatedAt = DateTimeHelper.GetUtcTime()
                                };


                                scopedDb.AccessLogs.Add(history);

                                smartLock.ElectricQuantity = record.ElectricQuantity;
                                smartLock.LastBatteryCheck = DateTimeHelper.GetUtcTime();
                            }
                            catch (Exception ex)
                            {

                            }

                        }

                        await scopedDb.SaveChangesAsync();
                    }
                });
            }
                
        }

        //api/TTLockWebHook/UploadRecord
        [HttpPost]
        public async Task<IActionResult> UploadRecord(TTLockUploadWebhookDto formData)
        {
            var response = new ResponseDTO<string>();
            try
            {
                if (!(formData.Records?.Any() ?? false))
                {
                    _logger.LogCritical($"formData no records found : {JsonConvert.SerializeObject(formData)}");
                    return Ok();
                }

                _logger.LogCritical($"formData records found : {JsonConvert.SerializeObject(formData)}");

                var records = JsonConvert.DeserializeObject<List<TTLockRecordDto>>(formData.Records) ?? new();
                if (!records.Any())
                {
                    response.SetMessage("No records after deserialization.");
                    return Ok();
                }
                var smartLock = await _context.SmartLocks.FirstOrDefaultAsync(a => a.TTLockId == formData.LockId);

                // 📝 Save history
                SaveHistoryAndUploadNotifyBackground(records, formData, smartLock);
                response.SetSuccess();

            }
            catch (Exception ex)
            {
                response.SetMessage($"Received Exception: {ex.Message}");
            }

            return Ok(response);
        }

        private void SaveHistoryAndUploadNotifyBackground(
     List<TTLockRecordDto> records,
     TTLockUploadWebhookDto formData,
     SmartLock? smartLock)
        {
            // Run fire-and-forget in background
            _ = Task.Run(async () =>
            {
                using (var scope = _serviceScopeFactory.CreateScope())
                {
                    var logger = scope.ServiceProvider.GetRequiredService<ILogger<TTLockWebHookController>>();
                    var scopedDb = scope.ServiceProvider.GetRequiredService<ResidoDbContext>();
                    var commonDBLogic = scope.ServiceProvider.GetRequiredService<CommonDBLogic>();

                    foreach (var record in records)
                    {
                        try
                        {
                            var history = new AccessLog
                            {
                                LockId = formData.LockId,
                                LockMac = string.Empty,
                                RecordType = record.RecordType,
                                RecordTypeDescription =
                                    appRecordTypeDescriptions.TryGetValue(record.RecordType, out var desc)
                                        ? desc : "Unknown",
                                Username = record.Username,
                                KeyboardPwd = record.KeyboardPwd,
                                Success = record.Success,
                                SmartLockId = smartLock.Id,
                                BatteryPercentage = record.ElectricQuantity,
                                LockEventLocalTime = record.LockDate,
                                ServerReceivedLocalTime = record.ServerDate,
                                LockEventUtcTime = DateTimeOffset.FromUnixTimeMilliseconds(record.LockDate).UtcDateTime,
                                ServerReceivedUtcTime = DateTimeOffset.FromUnixTimeMilliseconds(record.ServerDate).UtcDateTime,
                                CreatedAt = DateTimeHelper.GetUtcTime()
                            };


                            scopedDb.AccessLogs.Add(history);

                            if (smartLock != null)
                            {
                                smartLock.ElectricQuantity = record.ElectricQuantity;
                                smartLock.LastBatteryCheck = DateTimeHelper.GetUtcTime();
                            }
                        }
                        catch (Exception ex)
                        {
                            
                        }

                    }

                    await scopedDb.SaveChangesAsync();
                }
            });
        }
    }
}
