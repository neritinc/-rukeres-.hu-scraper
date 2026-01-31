<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Parameter;
use App\Models\Category;
use App\Models\Unit;

class ParameterSeeder extends Seeder
{
    public function run(): void
    {
        if (Category::count() === 0 || Unit::count() === 0) {
            $this->command->error('Nincsenek kategóriák vagy mértékegységek az adatbázisban!');
            return;
        }

        // név -> id map
        $cat = Category::pluck('id', 'category_name');
        $unit = Unit::pluck('id', 'unit_name');

        $resolveCategoryId = function (string $categoryName) use ($cat) {
            $categoryName = trim($categoryName);
            if (!isset($cat[$categoryName])) {
                throw new \Exception("Hiányzó category a categories táblában: '{$categoryName}'");
            }
            return $cat[$categoryName];
        };

        $resolveUnitId = function (?string $unitName) use ($unit) {
            $unitName = trim((string) $unitName);

            // nálad kötelező unit_id -> ha üres, legyen N/A
            if ($unitName === '') {
                $unitName = 'N/A';
            }

            if (!isset($unit[$unitName])) {
                throw new \Exception("Hiányzó unit a units táblában: '{$unitName}'");
            }

            return $unit[$unitName];
        };

        $parameters = [
            // Processor (ID: 1)
            ['parameter_name' => 'Clock Speed', 'category_name' => 'Processor', 'unit_name' => 'MHz'],
            ['parameter_name' => 'Turbo Clock Speed', 'category_name' => 'Processor', 'unit_name' => 'MHz'],
            ['parameter_name' => 'Core Count', 'category_name' => 'Processor', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Thread Count', 'category_name' => 'Processor', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'L2 Cache Size', 'category_name' => 'Processor', 'unit_name' => 'MB'],
            ['parameter_name' => 'L3 Cache Size', 'category_name' => 'Processor', 'unit_name' => 'MB'],
            ['parameter_name' => 'Thermal Design Power (TDP)', 'category_name' => 'Processor', 'unit_name' => 'W'],
            ['parameter_name' => 'Architecture', 'category_name' => 'Processor', 'unit_name' => 'N/A'],

            // Memory Module (ID: 2)
            ['parameter_name' => 'Memory Capacity', 'category_name' => 'Memory Module', 'unit_name' => 'GB'],
            ['parameter_name' => 'Memory Type', 'category_name' => 'Memory Module', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Bus Speed', 'category_name' => 'Memory Module', 'unit_name' => 'MHz'],
            ['parameter_name' => 'CAS Latency', 'category_name' => 'Memory Module', 'unit_name' => 'CL'],

            // Motherboard (ID: 3)
            ['parameter_name' => 'Socket', 'category_name' => 'Motherboard', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Chipset', 'category_name' => 'Motherboard', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Form Factor', 'category_name' => 'Motherboard', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Memory Slots', 'category_name' => 'Motherboard', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'M.2 Slots', 'category_name' => 'Motherboard', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Max Memory', 'category_name' => 'Motherboard', 'unit_name' => 'GB'],
            ['parameter_name' => 'Memory Type', 'category_name' => 'Motherboard', 'unit_name' => 'N/A'],
            ['parameter_name' => 'PCIe Slots', 'category_name' => 'Motherboard', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Wireless Networking', 'category_name' => 'Motherboard', 'unit_name' => 'N/A'],
            ['parameter_name' => 'RAID Support', 'category_name' => 'Motherboard', 'unit_name' => 'Yes/No'],

            // Graphics Card (ID: 4)
            ['parameter_name' => 'VRAM', 'category_name' => 'Graphics Card', 'unit_name' => 'GB'],
            ['parameter_name' => 'Core Clock', 'category_name' => 'Graphics Card', 'unit_name' => 'MHz'],
            ['parameter_name' => 'Boost Clock', 'category_name' => 'Graphics Card', 'unit_name' => 'MHz'],
            ['parameter_name' => 'Memory Clock', 'category_name' => 'Graphics Card', 'unit_name' => 'MHz'],
            ['parameter_name' => 'CUDA Cores', 'category_name' => 'Graphics Card', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'DirectX Version', 'category_name' => 'Graphics Card', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Thermal Design Power (TDP)', 'category_name' => 'Graphics Card', 'unit_name' => 'W'],
            ['parameter_name' => 'Cooling Fans', 'category_name' => 'Graphics Card', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Length', 'category_name' => 'Graphics Card', 'unit_name' => 'mm'],

            //STORAGE
            ['parameter_name' => 'Capacity', 'category_name' => 'Storage', 'unit_name' => 'TB'],
            ['parameter_name' => 'Cache', 'category_name' => 'Storage', 'unit_name' => 'MB'],
            ['parameter_name' => 'Maximum Read Speed', 'category_name' => 'Storage', 'unit_name' => 'MB/s'],
            ['parameter_name' => 'Maximum Write Speed', 'category_name' => 'Storage', 'unit_name' => 'MB/s'],
            ['parameter_name' => 'Connectivity Technology', 'category_name' => 'Storage', 'unit_name' => 'N/A'],

            //POWER SUPPLY
            ['parameter_name' => 'Wattage', 'category_name' => 'Power Supply', 'unit_name' => 'W'],
            ['parameter_name' => 'Efficiency Rating', 'category_name' => 'Power Supply', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Modular', 'category_name' => 'Power Supply', 'unit_name' => 'Full'],
            ['parameter_name' => 'Wattage', 'category_name' => 'Power Supply', 'unit_name' => 'W'],
            ['parameter_name' => 'Color', 'category_name' => 'Power Supply', 'unit_name' => '-'],

            //Cooling
            ['parameter_name' => 'Color', 'category_name' => 'Cooling', 'unit_name' => 'Color'],
            ['parameter_name' => 'Lighting', 'category_name' => 'Cooling', 'unit_name' => 'Color'],
            ['parameter_name' => 'Cooling', 'category_name' => 'Cooling', 'unit_name' => 'Cooled'],
            ['parameter_name' => 'Radiator Size', 'category_name' => 'Cooling', 'unit_name' => 'mm'],
            ['parameter_name' => 'Fan RPM', 'category_name' => 'Cooling', 'unit_name' => 'RPM'],
            ['parameter_name' => 'Noise Level', 'category_name' => 'Cooling', 'unit_name' => 'dB'],
            ['parameter_name' => 'CPU Socket', 'category_name' => 'Cooling', 'unit_name' => '-'],

            // Monitor (ID: 13)
            ['parameter_name' => 'Screen Size', 'category_name' => 'Monitor', 'unit_name' => 'inch'],
            ['parameter_name' => 'Resolution', 'category_name' => 'Monitor', 'unit_name' => 'N/A'],
            ['parameter_name' => 'Refresh Rate', 'category_name' => 'Monitor', 'unit_name' => 'Hz'],
            ['parameter_name' => 'Panel Type', 'category_name' => 'Monitor', 'unit_name' => 'N/A'],

            // Mouse (ID: 15)
            ['parameter_name' => 'Color', 'category_name' => 'Mouse', 'unit_name' => 'Color'],
            ['parameter_name' => 'Connectivity Technology', 'category_name' => 'Mouse', 'unit_name' => '-'],
            ['parameter_name' => 'DPI', 'category_name' => 'Mouse', 'unit_name' => 'DPI'],
            ['parameter_name' => 'Wireless', 'category_name' => 'Mouse', 'unit_name' => 'Yes/No'],
            ['parameter_name' => 'Battery Life', 'category_name' => 'Mouse', 'unit_name' => 'Hour'],

            // Case (ID: 8)
            ['parameter_name' => 'Type', 'category_name' => 'Case', 'unit_name' => 'Tower'],
            ['parameter_name' => 'Dimensions', 'category_name' => 'Case', 'unit_name' => ''],
            ['parameter_name' => 'Color', 'category_name' => 'Case', 'unit_name' => 'Color'],
            ['parameter_name' => 'Side Panel', 'category_name' => 'Case', 'unit_name' => 'Material'],
            ['parameter_name' => 'Max GPU Length', 'category_name' => 'Case', 'unit_name' => 'mm'],
            ['parameter_name' => 'Drive Bays', 'category_name' => 'Case', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Radiator Support', 'category_name' => 'Case', 'unit_name' => 'mm'],
            ['parameter_name' => 'Motherboard Form Factor', 'category_name' => 'Case', 'unit_name' => '-'],
            ['parameter_name' => 'Warranty', 'category_name' => 'Case', 'unit_name' => 'Year'],

            // Case Fan
            ['parameter_name' => 'Color', 'category_name' => 'Case Fan', 'unit_name' => '-'],
            ['parameter_name' => 'Fan Size', 'category_name' => 'Case Fan', 'unit_name' => 'mm'],
            ['parameter_name' => 'Fan height', 'category_name' => 'Case Fan', 'unit_name' => 'mm'],
            ['parameter_name' => 'Fan RPM', 'category_name' => 'Case Fan', 'unit_name' => 'RPM'],
            ['parameter_name' => 'Noise Level', 'category_name' => 'Case Fan', 'unit_name' => 'dB'],
            ['parameter_name' => 'Fan Connectors', 'category_name' => 'Case Fan', 'unit_name' => '4 pin'],
            ['parameter_name' => 'Warranty', 'category_name' => 'Case Fan', 'unit_name' => 'Year'],

            // Keyboard
            ['parameter_name' => 'Color', 'category_name' => 'Keyboard', 'unit_name' => '-'],
            ['parameter_name' => 'Switch Type', 'category_name' => 'Keyboard', 'unit_name' => '-'],
            ['parameter_name' => 'Mounting Type', 'category_name' => 'Keyboard', 'unit_name' => '-'],
            ['parameter_name' => 'Weight', 'category_name' => 'Keyboard', 'unit_name' => 'g'],
            ['parameter_name' => 'Battery Capacity', 'category_name' => 'Keyboard', 'unit_name' => 'mAh'],
            ['parameter_name' => 'Backlight', 'category_name' => 'Keyboard', 'unit_name' => '-'],
            ['parameter_name' => 'Key Amounts', 'category_name' => 'Keyboard', 'unit_name' => 'Pcs'],
            ['parameter_name' => 'Compatible', 'category_name' => 'Keyboard', 'unit_name' => '-'],
            ['parameter_name' => 'Connectivity Technology', 'category_name' => 'Keyboard', 'unit_name' => '-'],

            // Webcam

            ['parameter_name' => 'Resolution', 'category_name' => 'Webcam', 'unit_name' => '-'],
            ['parameter_name' => 'Connectivity Technology', 'category_name' => 'Webcam', 'unit_name' => '-'],
            ['parameter_name' => 'Connectivity Technology', 'category_name' => 'Webcam', 'unit_name' => '-'],
            ['parameter_name' => 'Focus Type', 'category_name' => 'Webcam', 'unit_name' => '-'],
            ['parameter_name' => 'FOV Angle', 'category_name' => 'Webcam', 'unit_name' => '°'],

            //Headset
            ['parameter_name' => 'Coldor', 'category_name' => 'Headset', 'unit_name' => '-'],
            ['parameter_name' => 'Frequency Range', 'category_name' => 'Headset', 'unit_name' => 'kHz'],
            ['parameter_name' => 'Microphone', 'category_name' => 'Headset', 'unit_name' => 'Yes/No'],
            ['parameter_name' => 'Active Noise Cancelling', 'category_name' => 'Headset', 'unit_name' => 'Yes/No'],
            ['parameter_name' => 'Impedance', 'category_name' => 'Headset', 'unit_name' => 'Ω'],

            //Speaker
            ['parameter_name' => 'Color', 'category_name' => 'Speaker', 'unit_name' => '-'],
            ['parameter_name' => 'Frequency Range', 'category_name' => 'Speaker', 'unit_name' => 'kHz'],
            ['parameter_name' => 'Tweeter', 'category_name' => 'Speaker', 'unit_name' => 'Teszt'],
            ['parameter_name' => 'Wattage', 'category_name' => 'Speaker', 'unit_name' => 'W'],
            ['parameter_name' => 'Crossover Frequency', 'category_name' => 'Speaker', 'unit_name' => 'kHz'],
            ['parameter_name' => 'Woofer Size', 'category_name' => 'Speaker', 'unit_name' => 'Teszt'],
            ['parameter_name' => 'Power Output', 'category_name' => 'Speaker', 'unit_name' => 'W'],
            ['parameter_name' => 'Bass Reflex System', 'category_name' => 'Speaker', 'unit_name' => 'Yes/No'],

                //Accessories & Tools
            ['parameter_name' => 'Length', 'category_name' => 'Accessory', 'unit_name' => 'm'],        // Kábelekhez (XLR, Extension)
            ['parameter_name' => 'Material', 'category_name' => 'Accessory', 'unit_name' => '-'],      // Egérpad, Csuklótámasz
            ['parameter_name' => 'Max Load', 'category_name' => 'Accessory', 'unit_name' => 'kg'],     // GPU tartóhoz
            ['parameter_name' => 'Thermal Conductivity', 'category_name' => 'Accessory', 'unit_name' => 'W/mK'], // Pasztához
            ['parameter_name' => 'Ports', 'category_name' => 'Accessory', 'unit_name' => 'Pcs'],       // Fan Hub-hoz
            ['parameter_name' => 'Torque', 'category_name' => 'Accessory', 'unit_name' => 'nm'],       // Csavarozógéphez
            ['parameter_name' => 'Connection Type', 'category_name' => 'Accessory', 'unit_name' => '-'], // Kontrollerhez (BT/Wired)
            ['parameter_name' => 'Dimensions', 'category_name' => 'Accessory', 'unit_name' => 'mm'], // Kontrollerhez (BT/Wired)




        ];

        foreach ($parameters as $p) {
            \DB::table('parameters')->updateOrInsert(
                ['parameter_name' => trim($p['parameter_name'])], // trim a biztonságért
                [
                    'category_id' => $resolveCategoryId($p['category_name']),
                    'unit_id' => $resolveUnitId($p['unit_name']),
                    'updated_at' => now(),
                    'created_at' => now(),
                ]
            );
        }
        $this->command->info('A paraméterek sikeresen hozzáadva!');
    }
}