<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.w3.org/1999/xhtml"
  xmlns:marc="http://www.bn.pt/standards/metadata/marcxml/1.0/">

	<xsl:output method="html"/>

	<xsl:param name="breakOnISBN" select="'n'"/>

	<xsl:variable name="breakToISBNBegin" select="'&amp;lt;p&gt;'"/>
	<xsl:variable name="breakToISBNEnd" select="'&amp;lt;/p&gt;'"/>
	<xsl:variable name="breakToISBNInter" select="'&amp;lt;br /&gt;'"/>

	<xsl:template match="/">
	<xsl:for-each select="marc:collection/marc:record">
		<p>
		<xsl:apply-templates select="marc:datafield[@tag='200']"/>
		<xsl:apply-templates select="marc:datafield[@tag='205']"/>
		<xsl:apply-templates select="marc:datafield[@tag='210']"/>
		<xsl:apply-templates select="marc:datafield[@tag='215']"/>
		<xsl:apply-templates select="marc:datafield[@tag='225']"/>
		<xsl:apply-templates select="marc:datafield[starts-with(@tag,'3')]"/>
		<xsl:choose>
			<xsl:when test="$breakOnISBN='y'">
				<xsl:call-template name="dettachedISBN"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="marc:datafield[@tag='010']"/>
			</xsl:otherwise>
		</xsl:choose>
		</p>
	</xsl:for-each>
	</xsl:template>

	<xsl:template name="isbdcomponent">
		<xsl:param name="punctuation"/>
		<xsl:param name="content" select="."/>
		<xsl:param name="ignore"/>
		<xsl:variable name="lcontent">
			<xsl:call-template name="clearNSx">
				<xsl:with-param name="content" select="$content" />
			</xsl:call-template>
		</xsl:variable>

		<xsl:choose>
			<xsl:when test="not(starts-with($lcontent,'='))">
				<xsl:value-of select="$punctuation"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text> </xsl:text>
			</xsl:otherwise>
		</xsl:choose>

		<xsl:variable name="left">
			<xsl:choose>
				<xsl:when test="substring($lcontent,string-length($lcontent)-2,3)='...'">
					<xsl:value-of select="$lcontent"/>
				</xsl:when>
				<xsl:when test="contains($ignore,substring($lcontent,string-length($lcontent),1))">
					<xsl:value-of
						select="normalize-space(substring($lcontent,1,string-length($lcontent)-1))"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="normalize-space($lcontent)"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="contains($ignore,substring($left,1,1))">
				<xsl:value-of
					select="normalize-space(substring($left,2))"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$left"/>
			</xsl:otherwise>
		</xsl:choose>
		
	</xsl:template>

	<xsl:template match="marc:datafield[@tag='200']">

		<xsl:for-each select="marc:subfield">

			<xsl:choose>

				<xsl:when test="@code='a'">
					<xsl:choose>
						<xsl:when test="preceding-sibling::marc:subfield[@code='a']">
							<xsl:text> ; </xsl:text>
						</xsl:when>
					</xsl:choose>
					<em>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
					</em>
				</xsl:when>

				<xsl:when test="@code='b'">
					<em>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' ['"/>
						<xsl:with-param name="ignore" select="']'"/>
					</xsl:call-template>
					<xsl:text>]</xsl:text>
					</em>
				</xsl:when>

				<xsl:when test="@code='c'">
					<xsl:text>. </xsl:text>
					<em>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
					</em>
				</xsl:when>

				<xsl:when test="@code='d'">
					<xsl:text> </xsl:text>
					<xsl:if test="not(starts-with(.,'='))">
						<xsl:text>= </xsl:text>
					</xsl:if>
					<em>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
					</em>
				</xsl:when>

				<xsl:when test="@code='e'">
					<em>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' : '"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
					</em>
				</xsl:when>

				<xsl:when test="@code='f'">
					<xsl:text> / </xsl:text>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='g'">
					<xsl:text> ; </xsl:text>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='h'">
					<xsl:text>. </xsl:text>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='i'">
					<xsl:choose>
						<xsl:when test="preceding-sibling::marc:subfield[@code='h']">
							<xsl:text>, </xsl:text>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>. </xsl:text>
						</xsl:otherwise>
					</xsl:choose>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation"/>
						<xsl:with-param name="ignore" select="':;./'"/>
					</xsl:call-template>
				</xsl:when>

			</xsl:choose>

		</xsl:for-each>

	</xsl:template>


	<xsl:template match="marc:datafield[@tag='205']">

		<xsl:text>. - </xsl:text>

		<xsl:for-each select="marc:subfield">
			<xsl:choose>

				<xsl:when test="@code='a'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="ignore" select="';,'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='d'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' = '"/>
						<xsl:with-param name="ignore" select="';,'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='f'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' / '"/>
						<xsl:with-param name="ignore" select="';,'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='g'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' ; '"/>
						<xsl:with-param name="ignore" select="';,'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='b'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="', '"/>
						<xsl:with-param name="ignore" select="';,'"/>
					</xsl:call-template>
				</xsl:when>

			</xsl:choose>
		</xsl:for-each>

	</xsl:template>

	<xsl:template match="marc:datafield[@tag='210']">

		<xsl:text>. - </xsl:text>

		<xsl:for-each select="marc:subfield">
			<xsl:choose>

				<xsl:when test="@code='a'">
					<xsl:if test="preceding-sibling::marc:subfield[@code='a']">
						<xsl:text> ; </xsl:text>
					</xsl:if>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="ignore" select="';:,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='b'">
					<xsl:value-of select="concat(' ',.)"/>
				</xsl:when>

				<xsl:when test="@code='c'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' : '"/>
						<xsl:with-param name="ignore" select="';:,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='d'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="', '"/>
						<xsl:with-param name="ignore" select="';:,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='e'">
					<xsl:choose>
						<xsl:when test="not(preceding-sibling::marc:subfield[@tag='e'])">
							<xsl:call-template name="isbdcomponent">
								<xsl:with-param name="punctuation" select="' ('"/>
								<xsl:with-param name="ignore" select="';:,()'"/>
							</xsl:call-template>
						</xsl:when>
						<xsl:otherwise>
							<xsl:call-template name="isbdcomponent">
								<xsl:with-param name="punctuation" select="' ; '"/>
								<xsl:with-param name="ignore" select="';:,()'"/>
							</xsl:call-template>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>

				<xsl:when test="@code='f'">
					<xsl:value-of select="concat(' ',.)"/>
				</xsl:when>

				<xsl:when test="@code='g'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' : '"/>
						<xsl:with-param name="ignore" select="';:,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='h'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="', '"/>
						<xsl:with-param name="ignore" select="';:,()'"/>
					</xsl:call-template>
				</xsl:when>

			</xsl:choose>

		</xsl:for-each>

		<xsl:if test="child::marc:subfield[@code='e']">
			<xsl:text>)</xsl:text>
		</xsl:if>

	</xsl:template>

	<xsl:template match="marc:datafield[@tag='215']">

		<xsl:text>. - </xsl:text>

		<xsl:for-each select="marc:subfield">
			<xsl:choose>

				<xsl:when test="@code='a'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="ignore" select="':;+'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='c'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation">
							<xsl:if test="position()!=1">
								<xsl:text> : </xsl:text>
							</xsl:if>
						</xsl:with-param>
						<xsl:with-param name="ignore" select="':;+'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='d'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation">
							<xsl:if test="position()!=1">
								<xsl:text> ; </xsl:text>
							</xsl:if>
						</xsl:with-param>
						<xsl:with-param name="ignore" select="':;+'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='e'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation">
							<xsl:if test="position()!=1">
								<xsl:text> + </xsl:text>
							</xsl:if>
						</xsl:with-param>
						<xsl:with-param name="ignore" select="':;+'"/>
					</xsl:call-template>
				</xsl:when>

			</xsl:choose>
		</xsl:for-each>

	</xsl:template>

	<xsl:template match="marc:datafield[@tag='225']">

		<xsl:if test="not(preceding-sibling::marc:datafield[@tag='225'])">
			<xsl:text>. - </xsl:text>
		</xsl:if>

		<xsl:for-each select="marc:subfield">
			<xsl:choose>

				<xsl:when test="@code='a'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="'('"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='d'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' = '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='e'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' : '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='f'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' / '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='x'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="', '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='v'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' ; '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='h'">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="'. '"/>
						<xsl:with-param name="ignore" select="':.;,()'"/>
					</xsl:call-template>
				</xsl:when>

				<xsl:when test="@code='i'">
					<xsl:choose>
						<xsl:when test="preceding-sibling::marc:subfield[@code='h']">
							<xsl:call-template name="isbdcomponent">
								<xsl:with-param name="punctuation" select="', '"/>
								<xsl:with-param name="ignore" select="':.;,()'"/>
							</xsl:call-template>
						</xsl:when>
						<xsl:otherwise>
							<xsl:call-template name="isbdcomponent">
								<xsl:with-param name="punctuation" select="'. '"/>
								<xsl:with-param name="ignore" select="':.;,()'"/>
							</xsl:call-template>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>

			</xsl:choose>
		</xsl:for-each>

		<xsl:text>)</xsl:text>

	</xsl:template>

	<xsl:template match="marc:datafield[starts-with(@tag,'3')]">

		<xsl:if test="marc:subfield[@code='a']">
			<xsl:text>. - </xsl:text>
		</xsl:if>

		<xsl:for-each select="marc:subfield[@code='a']">

			<xsl:choose>
				<xsl:when test="preceding-sibling::marc:subfield[@code='a']">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="'. '"/>
						<xsl:with-param name="ignore" select="'.'"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="ignore" select="'.'"/>
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>

		</xsl:for-each>

		<xsl:if test="@tag='326'">
			<xsl:for-each select="marc:subfield[@tag='b']">
				<xsl:value-of select="concat(', ',.)"/>
			</xsl:for-each>
		</xsl:if>

	</xsl:template>

	<xsl:template name="resourceIdentifier">
		<xsl:param name="domain"/>
		<xsl:param name="identifier"/>
		<xsl:param name="qualification"/>
		<xsl:param name="acquisition"/>
		<xsl:param name="keyTitle"/>

		<xsl:choose>
			<xsl:when test="string-length($identifier) &gt; 0">
				<xsl:text>. - </xsl:text>
				<xsl:value-of select="concat($domain,' ')"/>
				<xsl:value-of select="$identifier"/>
				<xsl:if test="string-length($qualification) &gt; 0">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' ('"/>
						<xsl:with-param name="content" select="$qualification"/>
						<xsl:with-param name="ignore" select="'()=:'"/>
					</xsl:call-template>
					<xsl:text>)</xsl:text>
				</xsl:if>
				<xsl:if test="string-length($keyTitle) &gt; 0">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' = '"/>
						<xsl:with-param name="content" select="$keyTitle"/>
						<xsl:with-param name="ignore" select="'():'"/>
					</xsl:call-template>
				</xsl:if>
				<xsl:if test="string-length($acquisition) &gt; 0">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="' : '"/>
						<xsl:with-param name="content" select="$acquisition"/>
						<xsl:with-param name="ignore" select="'()=:'"/>
					</xsl:call-template>
				</xsl:if>
			</xsl:when>
			<xsl:otherwise>
				<xsl:if test="string-length($acquisition) &gt; 0">
					<xsl:call-template name="isbdcomponent">
						<xsl:with-param name="punctuation" select="'. - '"/>
						<xsl:with-param name="content" select="$acquisition"/>
						<xsl:with-param name="ignore" select="':'"/>
					</xsl:call-template>
				</xsl:if>
			</xsl:otherwise>
		</xsl:choose>

	</xsl:template>

	<xsl:template name="identifiers">
		<xsl:param name="domain"/>

		<xsl:call-template name="resourceIdentifier">
			<xsl:with-param name="domain" select="$domain"/>
			<xsl:with-param name="identifier" select="marc:subfield[@code='a']"/>
			<xsl:with-param name="qualification" select="marc:subfield[@code='b']"/>
			<xsl:with-param name="acquisition" select="marc:subfield[@code='d']"/>
			<xsl:with-param name="keyTitle"/>
		</xsl:call-template>

		<xsl:for-each select="marc:subfield[@tag='z']">
			<xsl:call-template name="resourceIdentifier">
				<xsl:with-param name="domain" select="$domain"/>
				<xsl:with-param name="identifier" select="."/>
				<xsl:with-param name="qualification" select="'inválido'"/>
				<xsl:with-param name="acquisition"/>
				<xsl:with-param name="keyTitle"/>
			</xsl:call-template>
		</xsl:for-each>

	</xsl:template>

	<xsl:template match="marc:datafield[@tag='010']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="'ISBN'"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template name="dettachedISBN">
		<xsl:if test="marc:datafield[@tag='010']/marc:subfield[@code='a']">
			<xsl:value-of select="$breakToISBNBegin"/>
			<xsl:for-each select="marc:datafield[@tag='010']">
				<xsl:if test="marc:subfield[@code='a']">
					<xsl:if test="not(position()=1)">
						<xsl:value-of select="$breakToISBNInter"/>
					</xsl:if>
					<xsl:text>ISBN </xsl:text>
					<xsl:value-of select="marc:subfield[@code='a']"/>
				</xsl:if>
			</xsl:for-each>
			<xsl:value-of select="$breakToISBNEnd"/>
		</xsl:if>
	</xsl:template>

	<xsl:template match="marc:datafield[@tag='011']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="'ISSN'"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template match="marc:datafield[@tag='013']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="'ISMN'"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template match="marc/field[@tag='015']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="'ISRN'"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template match="marc:datafield[@tag='016']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="'ISRC'"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template match="marc:datafield[@tag='017']">
		<xsl:call-template name="identifiers">
			<xsl:with-param name="domain" select="marc:subfield[@tag='2']"/>
		</xsl:call-template>
	</xsl:template>

	<xsl:template name="clearNSx">
		<xsl:param name="content" />
		<xsl:choose>
			<xsl:when test="contains($content,'&amp;lt;')">
				<xsl:value-of select="translate(substring-before($content,'&amp;lt;'),'&gt;','')" />
				<xsl:variable name="next" select="substring-after($content,'&amp;lt;')" />
				<xsl:choose>
					<xsl:when test="contains($next,'&gt;')">
						<xsl:choose>
							<xsl:when
								test="contains($next,'=') and string-length(substring-before($next,'=')) &lt; string-length(substring-before($next,'&gt;'))">
								<xsl:value-of select="translate(substring-before($next,'='),'&amp;lt;','')"/>
								<xsl:call-template name="clearNSx">
									<xsl:with-param name="content" select="substring-after($next,'&gt;')"/>
								</xsl:call-template>
							</xsl:when>
							<xsl:otherwise>
								<xsl:value-of select="translate(substring-before($next,'&gt;'),'&amp;lt;','')" />
								<xsl:call-template name="clearNSx">
									<xsl:with-param name="content" select="substring-after($next,'&gt;')" />
								</xsl:call-template>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="translate($content,'&gt;','')" />
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:stylesheet>