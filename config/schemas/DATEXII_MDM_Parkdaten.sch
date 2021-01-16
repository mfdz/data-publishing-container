<schema xmlns="http://purl.oclc.org/dsdl/schematron" >
   <ns uri="http://datex2.eu/schema/2/2_0" prefix="dtx"/>
   <pattern id="occupancy_checks">
     <title>Occupancy checks</title>
     <rule context="dtx:parkingFacilityOccupancy">
       <assert test="current() &gt;= 0 and current() &lt;= 1">parkingFacilityOccupancy value <value-of select="."/> is not in range [0.0...1.0]</assert>
     </rule>
     <rule context="dtx:parkingAreayOccupancy">
       <assert test="current() &gt;= 0 and current() &lt;= 1">parkingAreayOccupancy value <value-of select="."/> is not in range [0.0...1.0]</assert>
     </rule>
   </pattern>
   <pattern id="override_checks">
     <title>Override checks</title>
     <rule context="dtx:parkingFacilityStatus[totalParkingCapacityLongTermOverride|totalParkingCapacityLongTermOverride|totalParkingCapacityShortTermOverride]">
       <assert role="warn" test="(sum(dtx:totalParkingCapacityLongTermOverride) + sum(dtx:totalParkingCapacityShortTermOverride) + sum(dtx:totalParkingCapacityOverride)) > 0">Sum of all given totalParkingXXXCapacityOverride of a parkingFacility should be greater than 0 for # <value-of select="dtx:parkingFacilityReference/@id"/></assert>
       <assert role="error" test="(sum(dtx:totalParkingCapacityLongTermOverride) + sum(dtx:totalParkingCapacityShortTermOverride)) &lt;= 2 * sum(dtx:totalParkingCapacityOverride)">Sum of all totalParkingCapacityShortTermOverride (<value-of select="dtx:totalParkingCapacityShortTermOverride"/>) and totalParkingCapacityLongTermOverride (<value-of select="dtx:totalParkingCapacityLongTermOverride"/>) should not exceed totalParkingCapacityOverride (<value-of select="dtx:totalParkingCapacityOverride"/>) for # <value-of select="dtx:parkingFacilityReference/@id"/>
		<value-of select="(dtx:totalParkingCapacityLongTermOverride + dtx:totalParkingCapacityShortTermOverride)"/>
       </assert>
     </rule>
   </pattern>
</schema>